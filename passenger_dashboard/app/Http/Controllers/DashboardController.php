<?php
namespace App\Http\Controllers;
use Illuminate\Http\Request;
use App\Models\Count;
use DB;

class DashboardController extends Controller
{
    public function index()
    {
        $data = Count::orderBy('timestamp', 'desc')->limit(20)->get();
        $avg_passengers = Count::avg('passengers');
        $peak_passengers = Count::max('passengers');
        $total_holidays = Count::where('holidays', 1)->count();
        // Add more queries as needed

        return view('dashboard', compact('data', 'avg_passengers', 'peak_passengers', 'total_holidays'));
    }
}