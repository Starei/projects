import pandas as pd
import numpy as np

from sklearn.preprocessing import StandardScaler

import torch
import warnings
from tqdm import trange


def lstm(combined_dataset):
    '''
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        warnings.warn('default', pd.errors.SettingWithCopyError)
    '''
    train_df, valid_df, test_df = data_preparation(combined_dataset)

    input_width, output_width = 2, 7
    window = WindowGenerator(
        input_width, label_width=output_width, shift=output_width, 
        shuffle=True, batch_size=512, label_columns=['precip'],
        train_df=train_df, valid_df=valid_df, test_df=test_df
    )

    hidden_dim = 128
    num_layers = 2
    input_dim = train_df.shape[1]
    model = LSTM(
        input_dim, hidden_dim, num_layers, 
        output_dim=output_width, dropout=0.3
    )

    loss_fn = torch.nn.BCELoss(reduction='mean')
    metric_fn = (lambda preds, labels: (preds.round() == labels).float().mean())
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    scheduler = torch.optim.lr_scheduler.StepLR(
        optimizer, step_size=5, gamma=0.9, verbose=False
    )

    early_stopping = 5 
    lstm_trainer = Trainer(
        model, epochs=1000, loss=loss_fn, metric=metric_fn,
        optim=optimizer, scheduler=scheduler, gradient_clipping=1e-8,
        early_stopping_delta=1e-4, early_stopping=early_stopping
    )
    lstm_trainer.fit(window.train, window.valid)
    print("VALIDATION: Loss={loss:.4f} | Metric={accuracy:.2f}".format_map({
        'loss': lstm_trainer.valid_loss[-early_stopping],
        'accuracy': lstm_trainer.valid_acc[-early_stopping]
    }))
    lstm_trainer.evaluate(window.test)

    inputs = torch.unsqueeze(torch.Tensor(test_df[-input_width:].values), dim=0)
    return [int(i) for i in
        (np.round(lstm_trainer.best_model(inputs).detach().numpy()[0], 2)*100)
    ]



def data_preparation(df):
    # TARGET
    # ==================================================================
    precip_sum_feats = [
        col for col in df.columns if col.endswith('precip_sum')
    ]
    precip_coder = (lambda x: 0 if x == 0.0 else 1)
    for col in precip_sum_feats:
        dist_side = col.removesuffix('precip_sum')
        df[dist_side + 'precip'] = df[col].map(precip_coder).astype(int)

    # FOURIER TERMS
    # ==================================================================
    def add_fourier_terms(df) -> pd.DataFrame:
        new_df = df.copy()
        timestamp_s = df.index.map(pd.Timestamp.timestamp)
        day = 24*60*60
        year = (365.2425)*day
        # summer-winter and spring-autumn
        new_df['year_sin'] = np.sin(timestamp_s * (2 * np.pi / year)) 
        new_df['year_cos'] = np.cos(timestamp_s * (2 * np.pi / year))
        return new_df
    
    df = add_fourier_terms(df)

    # WINDDIRECTION_DOMINANT
    # ==================================================================
    def convert_degrees_to_wind_direction(x):
        if 135 > x >= 45: return 0  # East
        elif 225 > x >= 135: return 1  # South
        elif 315 > x >= 225: return 2  # West
        else: return 3  # North

    winddir_feats = [
        col for col in df.columns if col.endswith('winddirection_dominant')
    ]
    for col in winddir_feats:
        df[col] = df[col].map(convert_degrees_to_wind_direction)

    # TEMPERATURE
    # ==================================================================
    temp_max_feats = [
        col for col in df.columns if col.endswith('temp_max')
    ]
    temp_min_feats = [
        col for col in df.columns if col.endswith('temp_min')
    ]
    for col1, col2 in zip(temp_max_feats, temp_min_feats):
        dist_side = col1.removesuffix('temp_max')
        df[dist_side + 'temp_aver'] = (df[col1] + df[col2]) / 2
        df[dist_side + 'temp_diff'] = df[col1] - df[col2]

    # SPLITING
    # ==================================================================
    def split_data(df, valid_size=.20, test_size=.10):
        train_size = 1 - (valid_size + test_size)
        n = len(df)
        train_df = df[:int(n*train_size)]
        valid_df = df[int(n*train_size) : int(n*(train_size+valid_size))]
        test_df = df[int(n*(1-test_size)):]
        return train_df, valid_df, test_df

    train_df, valid_df, test_df = split_data(df)

    # SCALING
    # ==================================================================
    precip_cols = [col for col in df.columns if col.endswith('precip')]
    non_scaled_feats = precip_cols + winddir_feats
    scaled_feats = list(set(df.columns) - set(non_scaled_feats))

    scaler = StandardScaler().set_output(transform='pandas')
    train_df[scaled_feats] = scaler.fit_transform(train_df[scaled_feats])
    valid_df[scaled_feats] = scaler.transform(valid_df[scaled_feats])
    test_df[scaled_feats] = scaler.transform(test_df[scaled_feats])

    return train_df, valid_df, test_df


class TimeseriesDataset:
    def __init__(self, data, sequence_length, sequence_stride):
        self.data = data
        self.sequence_length = sequence_length
        self.sequence_stride = sequence_stride
        
    def __len__(self):
        return len(self.data) // self.sequence_length
    
    def __iter__(self):
        total_len = len(self.data)-self.sequence_length
        for i in range(0, total_len, self.sequence_stride):
            yield np.array(self.data[i:i+self.sequence_length])


class WindowGenerator:  # An analogue of the batch
    def __init__(
        self, input_width, label_width, shift, 
        train_df, valid_df, test_df,
        batch_size=2**5, shuffle=True, label_columns=[]
    ):
        # Store the raw data.
        self.train_df = train_df
        self.valid_df = valid_df
        self.test_df = test_df

        # Work out the window parameters.
        self.input_width = input_width
        self.label_width = label_width
        self.shift = shift

        self.total_window_size = input_width + shift

        self.input_slice = slice(0, input_width)
        self.input_indices = np.arange(
            self.total_window_size
        )[self.input_slice]

        self.label_start = self.total_window_size - self.label_width
        self.labels_slice = slice(self.label_start, None)
        self.label_indices = np.arange(
            self.total_window_size
        )[self.labels_slice]
        
        # The other parameters
        self.batch_size = batch_size
        self.shuffle = shuffle
        
        # Work out the label column indices.
        self.label_columns = label_columns
        if label_columns:
            self.label_columns_indices = {
                name: i for i, name in enumerate(label_columns)
            }
        self.column_indices = {
            name: i for i, name in enumerate(train_df.columns)
        }

        
    def __repr__(self):
        return '\n'.join([
            f'Total window size: {self.total_window_size}',
            f'Input indices: {self.input_indices}',
            f'Label indices: {self.label_indices}',
            f'Label column name(s): {self.label_columns}'
        ])
    
    
    def split_window(self, features):
        """
        Splitting on inputs and labels allows to avoid knowledge of future
        predictor information because we will not know future weather
        conditions. We can only add some features of dates or time of year.
        """
        # we take n_arrays=input_width for inputs and the same for labels
        inputs = features[:, self.input_slice, :]
        labels = features[:, self.labels_slice, :]
        if self.label_columns:
            labels = torch.stack([
                # Selecting specified labels from each array in a batch
                labels[:, :, self.column_indices[name]] 
                for name in self.label_columns
            ], axis=-1)
        return inputs, labels
    
    def make_dataset(self, df):
        data = np.array(df, dtype=np.float32)
        # Splitting all data on batches
        ds = torch.utils.data.DataLoader(
            torch.from_numpy(np.array(list(
                TimeseriesDataset(
                    data=data, 
                    sequence_length=self.total_window_size,
                    sequence_stride=1
                )
            ))),
            shuffle=self.shuffle,
            batch_size=self.batch_size
        )
        ds = list(map(self.split_window, ds))
        return ds
    
    @property  # Calling function as a property (without brackets)
    def train(self):
        return self.make_dataset(self.train_df)

    @property
    def valid(self):
        return self.make_dataset(self.valid_df)

    @property
    def test(self):
        return self.make_dataset(self.test_df)
    

class LSTM(torch.nn.Module):
    def __init__(
        self, input_dim, hidden_dim, num_layers, output_dim, dropout=0.25
    ):
        super(LSTM, self).__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim

        # the number of hidden layers
        self.num_layers = num_layers
        self.dropout = dropout

        # batch_first=True causes input/output tensors to be of shape
        # (batch_dim, seq_dim, feature_dim)
        self.lstm = torch.nn.LSTM(
            input_dim, hidden_dim, num_layers, 
            batch_first=True, dropout=dropout
        )

        self.fc1 = torch.nn.Linear(hidden_dim, hidden_dim)
        self.fc2 = torch.nn.Linear(hidden_dim, output_dim)
        self.relu = torch.nn.ReLU()
        self.sigmoid = torch.nn.Sigmoid()

    def forward(self, x):
        # Initialize hidden state with zeros
        h0 = torch.zeros(
            self.num_layers, x.size(0), self.hidden_dim
        ).requires_grad_()

        # Initialize cell state
        c0 = torch.zeros(
            self.num_layers, x.size(0), self.hidden_dim
        ).requires_grad_()

        out, (hn, cn) = self.lstm(x, (h0.detach(), c0.detach()))

        out = out[:, -1, :]
        out = self.fc1(out)
        out = self.relu(out)
        out = self.fc2(out)
        return self.sigmoid(out)
    

class Trainer:
    def __init__(
        self, net, optim, loss, metric,
        lr=1e-3, verbose=True, epochs=10, device='cpu', early_stopping=3,
        scheduler=None, gradient_clipping=None, early_stopping_delta=0.0
    ):
        self.start_model, self.best_model = net, net
        self.lr, self.loss = lr, loss
        self.epochs, self.metric = epochs, metric
        self.device = torch.device(device)
        self.verbose, self.early_stopping = verbose, early_stopping
        self.optim, self.scheduler = optim, scheduler
        self.gradient_clipping = gradient_clipping
        self.train_loss, self.valid_loss = [], []
        self.train_acc, self.valid_acc = [], []
        self.early_stopping_delta = early_stopping_delta


    def fit(self, train_data, valid_data):
        model = self.start_model.to(self.device)
        if self.scheduler is not None:
            self.lrs = []
        pbar = trange(self.epochs)
        best_valid_loss, best_epoch = float('inf'), 0
        for epoch in pbar:
            # TRAINING
            model.train()
            epoch_loss, epoch_acc = 0, 0
            for step, (inputs, labels) in enumerate(train_data):
                inputs = inputs.to(self.device)
                labels = labels.to(self.device)
                
                preds = model(inputs)
                labels = torch.squeeze(labels, dim=2)
                loss_value = self.loss(preds, labels)
                metric_value = self.metric(preds, labels)
                
                epoch_loss += loss_value.item()
                epoch_acc += metric_value.item()
                
                loss_value.backward()
                
                    # Clip gradient
                if self.gradient_clipping:
                    torch.nn.utils.clip_grad_value_(
                        model.parameters(), self.gradient_clipping
                    )
                
                self.optim.step()
                
            self.optim.zero_grad()
            self.train_loss.append(epoch_loss / len(train_data))
            self.train_acc.append(epoch_acc / len(train_data))
            
            with torch.no_grad():
                # VALIDATION
                model.eval()
                epoch_loss, epoch_acc = 0, 0
                for step, (inputs, labels) in enumerate(valid_data):
                    inputs = inputs.to(self.device)
                    labels = labels.to(self.device)

                    preds = model(inputs)
                    labels = torch.squeeze(labels, dim=2)
                    loss_value = self.loss(preds, labels)
                    metric_value = self.metric(preds, labels)

                    epoch_loss += loss_value.item()
                    epoch_acc += metric_value.item()
                
                mean_valid_loss = epoch_loss / len(valid_data)
                mean_valid_acc = epoch_acc / len(valid_data)

                self.valid_loss.append(mean_valid_loss)
                self.valid_acc.append(mean_valid_acc)
                
            if self.verbose and epoch % 10 == 0:
                pbar.set_description(
                    f"loss={mean_valid_loss:.6f}|"
                    f"metric={mean_valid_acc:.2f}"
                )
                
            if mean_valid_loss < best_valid_loss - self.early_stopping_delta:
                best_valid_loss = mean_valid_loss
                best_epoch = epoch
                self.best_model = model
            elif epoch - best_epoch >= self.early_stopping:
                print(f"{self.early_stopping} epochs without improvements.") 
                print("Stop fitting...")
                break

            if self.scheduler is not None:
                self.scheduler.step()
                self.lrs.append(
                    self.optim.state_dict()['param_groups'][0]['lr']
                )


    def evaluate(self, test_data):
        # TEST
        self.best_model.eval()
        with torch.no_grad():
            test_loss, test_acc = 0, 0
            for step, (inputs, labels) in enumerate(test_data):
                inputs = inputs.to(self.device)
                labels = labels.to(self.device)

                preds = self.best_model(inputs)
                labels = torch.squeeze(labels, dim=2)
                loss_value = self.loss(preds, labels)
                metric_value = self.metric(preds, labels)
                
                test_loss += loss_value.item()
                test_acc += metric_value.item()
                
            print("TEST: ", end='')
            print(f"Loss={test_loss / len(test_data):.4f}", end=' | ')
            print(f"Metric={test_acc / len(test_data):.2f}")   