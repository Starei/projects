<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
//use Illuminate\Http\UserController;
/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
|
| Here is where you can register API routes for your application. These
| routes are loaded by the RouteServiceProvider within a group which
| is assigned the "api" middleware group. Enjoy building your API!
|
*/

Route::middleware('auth:sanctum')->get('/user', function (Request $request) {
    return $request->user();
});

Route::post("user-signup", "UserController@userSignUp");

Route::post("user-login", "UserController@userLogin");

Route::post("save-weather", "DataController@saveWeather");

Route::get("check-city/{city}", "DataController@checkCity");

Route::put("update/{city}", "DataController@updateData");

Route::get("user/{email}", "UserController@userDetail");

Route::get("users", "UserController@usersListing");

Route::delete("users/{id}", "UserController@userDelete");

Route::post("add-message", "DataController@addMessage");

Route::get("reports", "DataController@getReports");