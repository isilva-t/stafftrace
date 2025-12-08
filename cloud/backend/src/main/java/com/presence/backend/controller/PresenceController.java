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

}
