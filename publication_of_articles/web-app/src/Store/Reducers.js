import { ACTION_SET_AUTH_LOGIN, ACTION_SET_AUTH_STATUS } from './Actions'

const initialState = {
    login: '',
    authorized: false,
  }

export const rootReducer = (state = initialState, action) => {
    switch (action.type) {
        case ACTION_SET_AUTH_LOGIN:
            return { 
                ...state,
                login: action.payload 
            }
        case ACTION_SET_AUTH_STATUS:
            return { 
                ...state,
                authorized: action.payload 
            }
        default:
              
    }
    return state
}
