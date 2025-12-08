package com.presence.backend.controller;

import com.presence.backend.model.CurrentStatus;
import com.presence.backend.model.DailyPresence;
import com.presence.backend.model.dto.*;
import com.presence.backend.repository.CurrentStatusRepository;
import com.presence.backend.repository.DailyPresenceRepository;
import com.presence.backend.service.JwtService;
import com.presence.backend.service.NameMappingService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class PresenceController {

	@Autowired
	private CurrentStatusRepository currentStatusRepository;

	@Autowired
	private DailyPresenceRepository dailyPresenceRepository;

	@Autowired
	private JwtService jwtService;

	@Autowired
	private NameMappingService nameMappingService;

	@PostMapping("/presence")
	public ResponseEntity<String> receivePresence(@RequestBody PresenceRequest request) {
		
		for (PresenceRequest.PresenceData data : request.getPresenceData()) {
			LocalDate date = LocalDate.parse(data.getDate());

			//find or create daily presence record
			DailyPresence daily = dailyPresenceRepository
								.findByEmployeeInAndDate(data.getEmployeeId(), date)
								.orElse(new DailyPresence());

			boolean isNew = daily.getId() == null;

			daily.setEmployeeId(data.getEmployeeId());
			daily.setEmployeeName(data.getEmployeeName());
			daily.setFakeName(data.getFakeName());
			daily.setDate(date);

			LocalTime newFirstSeen = LocalTime.parse(data.getFirstSeen());
			if (isNew || daily.getFirstSeen() == null
				|| newFirstSeen.isBefore(daily.getFirstSeen())) {
				daily.setFirstSeen(newFirstSeen);
			}
			
			LocalTime newLastSeen = LocalTime.parse(data.getLastSeen());
			if (isNew || daily.getLastSeen() == null
				|| newLastSeen.isAfter(daily.getLastSeen()) {
				daily.setLastSeen(newLastSeen);
			}

			int currentMinutes = daily.getTotalMinutes() != null ? daily.getTotalMinutes() : 0;
			daily.setTotalMinutes(currentMinutes + data.getMinutesOnline());
			daily.setHoursPresent(daily.getTotalMinutes() / 60.0);

			// set timestamps
			if (isNew) {
				daily.setCreatedAt(LocalDateTime.now());
			}
			daily.setUpdatedAt(LocalDateTime.now());

			dailyPresenceRepository.save(daily);
		}
		return ResponseEntity.ok("Presence data received");
	}

}
