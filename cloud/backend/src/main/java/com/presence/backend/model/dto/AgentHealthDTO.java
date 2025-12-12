package com.presence.backend.model.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@AllArgsConstructor
public class AgentHealthDTO {
	private String siteId;
	private LocalDateTime lastHeartbeat;
	private Boolean hasLastHeartbeat;
}
