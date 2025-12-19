package com.presence.backend.controller;

import com.presence.backend.model.CurrentStatus;
import com.presence.backend.model.DailyPresence;
import com.presence.backend.model.AgentDowntime;
import com.presence.backend.repository.AgentDowntimeRepository;
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
import java.util.Map;
import java.util.stream.Collectors;
import java.time.DayOfWeek;
import java.time.format.TextStyle;
import java.util.Locale;
import java.util.ArrayList;

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

	@Autowired
	private AgentDowntimeRepository agentDowntimeRepository;

	@PostMapping("/presence")
	public ResponseEntity<String> receivePresence(@RequestBody PresenceRequest request) {

		if (request.getAgentDowntimes() != null && !request.getAgentDowntimes().isEmpty()) {
			for (PresenceRequest.AgentDowntimeData dtData : request.getAgentDowntimes()) {
				AgentDowntime downtime = new AgentDowntime();

				String startStr = dtData.getDowntimeStart()
						.replace("Z", "")
						.replaceAll("\\+00:00$", "");
				String endStr = dtData.getDowntimeEnd()
						.replace("Z", "")
						.replaceAll("\\+00:00$", "");

				downtime.setDowntimeStart(LocalDateTime.parse(startStr));
				downtime.setDowntimeEnd(LocalDateTime.parse(endStr));
				downtime.setCreatedAt(LocalDateTime.now());
				agentDowntimeRepository.save(downtime);
			}
		}

		for (PresenceRequest.PresenceData data : request.getPresenceData()) {
			LocalDate date = LocalDate.parse(data.getDate());

			// find or create daily presence record
			DailyPresence daily = dailyPresenceRepository
					.findByEmployeeIdAndDate(data.getEmployeeId(), date)
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
					|| newLastSeen.isAfter(daily.getLastSeen())) {
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

	@GetMapping("/current")
	public ResponseEntity<List<EmployeeStatusDTO>> getCurrentStatus(
			@RequestHeader(value = "Authorization", required = false) String authHeader) {

		boolean isAuthenticated = false;
		if (authHeader != null && authHeader.startsWith("Bearer ")) {
			String token = authHeader.substring(7);
			isAuthenticated = jwtService.validateToken(token);
		}

		List<CurrentStatus> statuses = currentStatusRepository.findAll();

		boolean finalIsAuthenticated = isAuthenticated;
		List<EmployeeStatusDTO> result = statuses.stream()
				.map(status -> new EmployeeStatusDTO(
						status.getEmployeeId(),
						nameMappingService.getDisplayName(
								status.getEmployeeName(),
								status.getFakeName(),
								finalIsAuthenticated),
						status.getIsPresent(),
						status.getCurrentArea(),
						status.getLastSeen()))
				.collect(Collectors.toList());

		return ResponseEntity.ok(result);
	}

	@GetMapping("/daily")
	public ResponseEntity<List<DailyPresence>> getDailyReport(
			@RequestParam String date,
			@RequestHeader(value = "Authorization", required = false) String authHeader) {

		boolean isAuthenticated = false;
		if (authHeader != null && authHeader.startsWith("Bearer ")) {
			String token = authHeader.substring(7);
			isAuthenticated = jwtService.validateToken(token);
		}

		LocalDate queryDate = LocalDate.parse(date);
		List<DailyPresence> records = dailyPresenceRepository.findByDate(queryDate);

		// apply name mapping
		boolean finalIsAuthenticated = isAuthenticated;
		records.forEach(record -> {
			String displayName = nameMappingService.getDisplayName(
					record.getEmployeeName(),
					record.getFakeName(),
					finalIsAuthenticated);
			record.setEmployeeName(displayName);

			double hours = calculateTimeSpan(record.getFirstSeen(), record.getLastSeen());
			record.setHoursPresent(hours);
		});

		return ResponseEntity.ok(records);
	}

	@GetMapping("/monthly")
	public ResponseEntity<List<MonthlyPresenceDTO>> getMonthlyReport(
			@RequestParam int year,
			@RequestParam int month,
			@RequestHeader(value = "Authorization", required = false) String authHeader) {

		boolean isAuthenticated = false;
		if (authHeader != null && authHeader.startsWith("Bearer ")) {
			String token = authHeader.substring(7);
			isAuthenticated = jwtService.validateToken(token);
		}

		LocalDate startDate = LocalDate.of(year, month, 1);
		LocalDate endDate = startDate.plusMonths(1).minusDays(1);

		List<DailyPresence> records = dailyPresenceRepository
				.findByDateBetween(startDate, endDate);

		Map<Integer, List<DailyPresence>> groupByEmployee = records.stream()
				.collect(Collectors.groupingBy(DailyPresence::getEmployeeId));

		boolean finalIsAuthenticated = isAuthenticated;
		List<MonthlyPresenceDTO> result = groupByEmployee.entrySet().stream()
				.map(entry -> {
					Integer employeeId = entry.getKey();
					List<DailyPresence> employeeRecords = entry.getValue();

					DailyPresence firstRecord = employeeRecords.get(0);
					String displayName = nameMappingService.getDisplayName(
							firstRecord.getEmployeeName(),
							firstRecord.getFakeName(),
							finalIsAuthenticated);

					double totalHours = employeeRecords.stream()
							.mapToDouble(record -> {
								LocalTime firstSeen = record.getFirstSeen();
								LocalTime lastSeen = record.getLastSeen();
								return calculateTimeSpan(firstSeen, lastSeen);
							})
							.sum();

					int daysPresent = employeeRecords.size();
					double avgHoursPerDay = totalHours / daysPresent;

					return new MonthlyPresenceDTO(
							employeeId,
							displayName,
							totalHours,
							daysPresent,
							avgHoursPerDay);
				})
				.collect(Collectors.toList());

		return ResponseEntity.ok(result);
	}

	@GetMapping("/employee/{employeeId}/monthly")
	public ResponseEntity<EmployeeMonthlyDetailDTO> getEmployeeMonthlyDetail(
			@PathVariable Integer employeeId,
			@RequestParam int year,
			@RequestParam int month,
			@RequestHeader(value = "Authorization", required = false) String authHeader) {

		boolean isAuthenticated = false;
		if (authHeader != null && authHeader.startsWith("Bearer ")) {
			String token = authHeader.substring(7);
			isAuthenticated = jwtService.validateToken(token);
		}
		LocalDate startDate = LocalDate.of(year, month, 1);
		LocalDate endDate = startDate.plusMonths(1).minusDays(1);
		int daysInMonth = endDate.getDayOfMonth();

		List<DailyPresence> records = dailyPresenceRepository
				.findByEmployeeIdAndDateBetween(employeeId, startDate, endDate);

		Map<LocalDate, DailyPresence> recordMap = records.stream()
				.collect(Collectors.toMap(DailyPresence::getDate, r -> r));

		String employeeName = "Unknown";
		String fakeName = "Unknown";
		if (!records.isEmpty()) {
			DailyPresence firstRecord = records.get(0);
			employeeName = firstRecord.getEmployeeName();
			fakeName = firstRecord.getFakeName();
		}

		String displayName = nameMappingService.getDisplayName(
				employeeName, fakeName, isAuthenticated);

		List<DailyDetailDTO> dailyDetails = new ArrayList<>();
		double totalHours = 0.0;
		int daysPresent = 0;

		for (int day = 1; day <= daysInMonth; day++) {
			LocalDate currentDate = LocalDate.of(year, month, day);
			DayOfWeek dayOfWeek = currentDate.getDayOfWeek();
			String dayName = dayOfWeek.getDisplayName(TextStyle.FULL, Locale.ENGLISH);

			DailyPresence record = recordMap.get(currentDate);

			String firstSeen = null;
			String lastSeen = null;
			double hours = 0.0;
			String status;

			if (record != null) {
				firstSeen = record.getFirstSeen() != null ? record.getFirstSeen().toString() : null;
				lastSeen = record.getLastSeen() != null ? record.getLastSeen().toString() : null;
				hours = calculateTimeSpan(firstSeen, lastSeen);

				if (hours >= 8.0) {
					status = "Full day";
				} else if (hours > 0) {
					status = "Partial";
				} else {
					status = "Absent";
				}

				totalHours += hours;
				if (hours > 0) {
					daysPresent++;
				}
			} else {
				if (dayOfWeek == DayOfWeek.SATURDAY || dayOfWeek == DayOfWeek.SUNDAY) {
					status = "Weekend";
				} else {
					status = "Absent";
				}
			}

			dailyDetails.add(new DailyDetailDTO(
					currentDate.toString(),
					dayName,
					firstSeen,
					lastSeen,
					hours,
					status));
		}

		EmployeeMonthlyDetailDTO result = new EmployeeMonthlyDetailDTO(
				employeeId,
				displayName,
				year,
				month,
				dailyDetails,
				totalHours,
				daysPresent);

		return ResponseEntity.ok(result);
	}

	@GetMapping("/downtimes")
	public ResponseEntity<List<AgentDowntime>> getDowntimes(@RequestParam String date) {

		LocalDate queryDate = LocalDate.parse(date);
		LocalDateTime startOfDay = queryDate.atStartOfDay();
		LocalDateTime endOfDay = queryDate.plusDays(1).atStartOfDay();

		List<AgentDowntime> downtimes = agentDowntimeRepository.findByDowntimeStartBetween(startOfDay, endOfDay);

		return ResponseEntity.ok(downtimes);
	}

	private double calculateTimeSpan(String firstSeen, String lastSeen) {
		if (firstSeen == null || lastSeen == null) {
			return 0.0;
		}
		String[] firstParts = firstSeen.split(":");
		String[] lastParts = lastSeen.split(":");

		int firstHour = Integer.parseInt(firstParts[0]);
		int firstMinute = Integer.parseInt(firstParts[1]);

		int lastHour = Integer.parseInt(lastParts[0]);
		int lastMinute = Integer.parseInt(lastParts[1]);

		int firstMinutes = firstHour * 60 + firstMinute;
		int lastMinutes = lastHour * 60 + lastMinute;

		return (lastMinutes - firstMinutes) / 60.0;
	}

	private double calculateTimeSpan(LocalTime firstSeen, LocalTime lastSeen) {
		if (firstSeen == null || lastSeen == null) {
			return 0.0;
		}

		int firstMinutes = firstSeen.getHour() * 60 + firstSeen.getMinute();
		int lastMinutes = lastSeen.getHour() * 60 + lastSeen.getMinute();

		return (lastMinutes - firstMinutes) / 60.0;
	}
}
