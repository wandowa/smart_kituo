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
                        <p><?php echo e(round($avg_passengers, 2)); ?></p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-white bg-success mb-3">
                    <div class="card-body">
                        <h5>Peak Passengers</h5>
                        <p><?php echo e($peak_passengers); ?></p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-white bg-warning mb-3">
                    <div class="card-body">
                        <h5>Holiday Counts</h5>
                        <p><?php echo e($total_holidays); ?></p>
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
                    labels: [<?php $__currentLoopData = $data; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $item): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?> '<?php echo e($item->timestamp); ?>', <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>],
                    datasets: [{
                        label: 'Passengers',
                        data: [<?php $__currentLoopData = $data; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $item): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?> <?php echo e($item->passengers); ?>, <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>],
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
                        <?php $__currentLoopData = $data; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $item): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
                        <tr>
                            <td><?php echo e($item->timestamp); ?></td>
                            <td><?php echo e($item->passengers); ?></td>
                            <td><?php echo e($item->day); ?></td>
                            <td><?php echo e($item->date); ?></td>
                            <td><?php echo e($item->weather); ?></td>
                            <td><?php echo e($item->time_value); ?></td>
                            <td><?php echo e($item->peak_hours ? 'Yes' : 'No'); ?></td>
                            <td><?php echo e($item->weekends ? 'Yes' : 'No'); ?></td>
                            <td><?php echo e($item->holidays ? 'Yes' : 'No'); ?></td>
                        </tr>
                        <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html><?php /**PATH C:\Users\Wandowa\Documents\PROJECTS\Wandowa Final Year Project\Camera Detection\passenger_dashboard\resources\views/dashboard.blade.php ENDPATH**/ ?>