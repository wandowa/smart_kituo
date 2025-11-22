<!DOCTYPE html>
<html>
<head>
    <title>Passenger Admin Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <h1>Passenger Insights Dashboard</h1>

        <!-- Live Video Widget -->
        <div class="card mb-4">
            <div class="card-header">Live Video Feed</div>
            <div class="card-body">
                <img src="http://localhost:5000/video_feed" alt="Live Passenger Detection" style="width:100%;">
            </div>
        </div>

        <!-- Metric Widgets (Cards) -->
        <div class="row">
            <div class="col-md-3">
                <div class="card text-white bg-primary mb-3">
                    <div class="card-body">
                        <h5>Avg Passengers</h5>
                        <p>{{ round($avg_passengers, 2) }}</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-white bg-success mb-3">
                    <div class="card-body">
                        <h5>Peak Passengers</h5>
                        <p>{{ $peak_passengers }}</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-white bg-warning mb-3">
                    <div class="card-body">
                        <h5>Holiday Counts</h5>
                        <p>{{ $total_holidays }}</p>
                    </div>
                </div>
            </div>
            <!-- Add more cards for weather, peak hours, etc. -->
        </div>

        <!-- Chart Widget: Passengers Over Time -->
        <div class="card mb-4">
            <div class="card-header">Passengers Over Time</div>
            <div class="card-body">
                <canvas id="passengerChart"></canvas>
            </div>
        </div>
        <script>
            var ctx = document.getElementById('passengerChart').getContext('2d');
            var chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [@foreach($data as $item) '{{ $item->timestamp }}', @endforeach],
                    datasets: [{
                        label: 'Passengers',
                        data: [@foreach($data as $item) {{ $item->passengers }}, @endforeach],
                        borderColor: 'rgba(75, 192, 192, 1)',
                        fill: false
                    }]
                },
                options: { scales: { y: { beginAtZero: true } } }
            });
        </script>

        <!-- Table Widget: Recent Data -->
        <div class="card">
            <div class="card-header">Recent Insights</div>
            <div class="card-body">
                <table class="table">
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Passengers</th>
                            <th>Day</th>
                            <th>Date</th>
                            <th>Weather</th>
                            <th>Time</th>
                            <th>Peak Hours</th>
                            <th>Weekends</th>
                            <th>Holidays</th>
                        </tr>
                    </thead>
                    <tbody>
                        @foreach($data as $item)
                        <tr>
                            <td>{{ $item->timestamp }}</td>
                            <td>{{ $item->passengers }}</td>
                            <td>{{ $item->day }}</td>
                            <td>{{ $item->date }}</td>
                            <td>{{ $item->weather }}</td>
                            <td>{{ $item->time_value }}</td>
                            <td>{{ $item->peak_hours ? 'Yes' : 'No' }}</td>
                            <td>{{ $item->weekends ? 'Yes' : 'No' }}</td>
                            <td>{{ $item->holidays ? 'Yes' : 'No' }}</td>
                        </tr>
                        @endforeach
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>