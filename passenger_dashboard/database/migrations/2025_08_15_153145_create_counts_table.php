<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up()
{
    Schema::create('counts', function (Blueprint $table) {
        $table->id();
        $table->timestamp('timestamp');
        $table->integer('passengers');
        $table->string('day');
        $table->date('date');
        $table->string('weather');
        $table->time('time_value');
        $table->boolean('peak_hours');
        $table->boolean('weekends');
        $table->boolean('holidays');
        $table->timestamps();
    });
}
    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('counts');
    }
};
