package com.presence.backend.controller;

import com.presence.backend.model.CurrentStatus;
import com.presence.backend.model.dto.HeartbeatRequest;
import com.presence.backend.repository.CurrentStatusRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class HeartbeatController {
	
	@Autowired
	private CurrentStatusRepository currentStatusRepository;

	@PostMapping("/heartbeat")
	public ResponseEntity<String> receiveHeartbeat(@RequestBody HeartbeatRequest request) {
	
		LocalDateTimwe now = LocalDateTime.now();
		LocalDateTime tenMinutesAgo = now.minusMinutes(10);

		// mark devices in list as present
		for (HeartbeatRequest.DeviceOnline device : request.getDevicesOnline()) {
			CurrentStatus status = currentStatusRepository
						.findByEmployeeId(device.getEmployeeId())
						.orElse(new CurrentStatus());

			status.setEmployeeId(device.getEmployeeId());
			status.setEmployeeName(device.getEmployeeName());
			status.setFakename(device.getFaceName());
			status.setIsPresent(true);
			status.setCurrentArea(device.getArea());
			status.setLastSeen(now);
			status.setUpdatedAt(now);

			currentStatusRepository.save(status);
		}

		// makr devices not in list as absent (if not seen in 10 minutes)
		currentStatusRepository.findAll().forEach(status-> {
			boolean inCurrentList = request.getDevicesOnline().stream()
					.anyMatch(d -> d.getEmployeeId().equals(status.getEmployeeId()))

			if (!inCurrentList && status.getLastSeen().isBefore(tenMinutesAgo)) {
				status.setIsPresent(false);
				status.setUpdatedAt(now);
				currentStatusRepository.save(status);
			}
		});

		return ResponseEntity.ok("Heartbeat received");
	}
}
