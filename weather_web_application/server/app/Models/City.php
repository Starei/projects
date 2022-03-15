<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class City extends Model
{
    use HasFactory;

    protected $fillable = [
        'city',
        'country',
        'temperature',
        'fellslike',
        'pressure',
        'weather',
        'update_at',
    ];

    public $timestamps = false;
}
