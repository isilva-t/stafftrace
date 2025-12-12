package com.presence.backend.model;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;
import java.time.LocalDateTime;

@Data
@Document(collection = "agent_health")
public class AgentHealth {
	@Id
	private String id;

	@Indexed(unique = true)
	private String siteId;

	private LocalDateTime lastHeartbeat;
	private LocalDateTime updatedAt;
}
