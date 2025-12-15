package com.presence.backend.controller;

import com.presence.backend.model.CurrentStatus;
import com.presence.backend.model.AgentHealth;
import com.presence.backend.repository.AgentHealthRepository;
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

	@Autowired
	private AgentHealthRepository agentHealthRepository;

	@PostMapping("/heartbeat")
	public ResponseEntity<String> receiveHeartbeat(@RequestBody HeartbeatRequest request) {

		LocalDateTime now = LocalDateTime.now();

		// mark devices in list as present
		for (HeartbeatRequest.DeviceOnline device : request.getDevicesOnline()) {
			CurrentStatus status = currentStatusRepository
					.findByEmployeeId(device.getEmployeeId())
					.orElse(new CurrentStatus());

			status.setEmployeeId(device.getEmployeeId());
			status.setEmployeeName(device.getEmployeeName());
			status.setFakeName(device.getFakeName());
			status.setIsPresent(device.getIsPresent());
			status.setCurrentArea(device.getArea());
			status.setLastSeen(now);
			status.setUpdatedAt(now);

			currentStatusRepository.save(status);
		}

		AgentHealth agentHealth = agentHealthRepository
				.findBySiteId(request.getSiteId())
				.orElse(new AgentHealth());

		agentHealth.setSiteId(request.getSiteId());
		agentHealth.setLastHeartbeat(now);
		agentHealth.setUpdatedAt(now);

		agentHealthRepository.save(agentHealth);

		return ResponseEntity.ok("Heartbeat received");
	}
}
