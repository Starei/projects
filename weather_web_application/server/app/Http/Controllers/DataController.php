<?php

namespace App\Http\Controllers;

use Carbon\Carbon;
use App\Models\City;
use App\Models\Report;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;
use Illuminate\Support\Str;

class DataController extends Controller
{
    private $status_code = 200;

    public function saveWeather(Request $request) {
        $validator = Validator::make($request->all(), [
            "city" => "required",
            "country" => "required",
            "temperature" => "required",
            "fellslike" => "required",
            "pressure" => "required",
            "weather" => "required",
            "update_at" => "required",
        ]);

        if($validator->fails()) {
            return response()->json(["message" => "validation_error", "errors" => $validator->errors()]);
        }

        $cityDataArray          =       array (
            "city"              =>          $request->city,
            "country"           =>          $request->country,
            "temperature"       =>          $request->temperature,
            "fellslike"         =>          $request->fellslike,
            "pressure"          =>          $request->pressure,
            "weather"           =>          $request->weather,
            "update_at"         =>          $request->update_at
        );

        $city = City::create($cityDataArray);

        if(!is_null($city)) { 
            return response()->json(["message" => "Completed successfully"]);
        }

        else {
            return response()->json(["message" => "Failed to add"]);
        }
         
    }
    
    public function checkCity($city) {
        $data = array();
        $data = City::where("city", $city)->first();

        if (!is_null($data)) {
            return response()->json(["status" => 200, "data" => $data]);
        }
        else {
            return response()->json(["status" => "failed", "message" => "Whoops!"]);
        }
    }

    public function updateData(Request $request, $city) {
        $validator = Validator::make($request->all(), [
            "city" => "required",
            "country" => "required",
            "temperature" => "required",
            "fellslike" => "required",
            "pressure" => "required",
            "weather" => "required",
            "update_at" => "required",
        ]);

        if($validator->fails()) {
            return response()->json(["message" => "validation_error", "errors" => $validator->errors()]);
        }

        $cityDataArray          =       array (
            "city"              =>          $request->city,
            "country"           =>          $request->country,
            "temperature"       =>          $request->temperature,
            "fellslike"         =>          $request->fellslike,
            "pressure"          =>          $request->pressure,
            "weather"           =>          $request->weather,
            "update_at"         =>          $request->update_at
        );

        $update_city = City::where("city", $city)->update($cityDataArray);

        if(!is_null($update_city)) { 
            return response()->json(["message" => "Completed successfully"]);
        }

        else {
            return response()->json(["message" => "Failed to add"]);
        }
    }

    public function addMessage(Request $request) {
        $validator = Validator::make($request->all(), [
            "type" => "required",
            "level" => "required",
            "message" => "required",
        ]);

        if($validator->fails()) {
            return response()->json(["message" => "validation_error", "errors" => $validator->errors()]);
        }

        $messageDataArray          =       array (
            "type"              =>          $request->type,
            "level"           =>          $request->level,
            "message"       =>          $request->message,
        );

        $message = Report::create($messageDataArray);

        if(!is_null($message)) { 
            return response()->json(["message" => "Completed successfully"]);
        }

        else {
            return response()->json(["message" => "Failed to add"]);
        }
    }

    public function getReports()
    {
        $reports       =       Report::all();
        if(count($reports) > 0) {
            return response()->json(["status" => 200, "success" => true, "count" => count($reports), "data" => $reports]);
        }
        else {
            return response()->json(["status" => "failed", "success" => false, "message" => "Whoops! no record found"]);
        }
    }
}
