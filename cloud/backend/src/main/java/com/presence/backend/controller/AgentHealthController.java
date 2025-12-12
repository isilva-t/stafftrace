package com.presence.backend.controller;

import com.presence.backend.model.AgentHealth;
import com.presence.backend.model.dto.AgentHealthDTO;
import com.presence.backend.repository.AgentHealthRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class AgentHealthController {

	@Autowired
	private AgentHealthRepository agentHealthRepository;

	@GetMapping("/agent-health")
	public ResponseEntity<List<AgentHealthDTO>> getAgentHealth() {

		List<AgentHealth> allAgents = agentHealthRepository.findAll();

		if (allAgents.isEmpty()) {
			return ResponseEntity.ok(new ArrayList<>());
		}

		List<AgentHealthDTO> dtos = allAgents.stream()
				.map(health -> new AgentHealthDTO(
						health.getSiteId(),
						health.getLastHeartbeat(),
						true))
				.collect(Collectors.toList());

		return ResponseEntity.ok(dtos);
	}
}
