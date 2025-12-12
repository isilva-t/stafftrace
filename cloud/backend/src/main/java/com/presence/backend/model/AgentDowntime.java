package com.presence.backend.model;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import java.time.LocalDateTime;

@Data
@Document(collection = "agent_downtimes")
public class AgentDowntime {
	@Id
	private String id;

	private LocalDateTime downtimeStart;
	private LocalDateTime downtimeEnd;
	private LocalDateTime createdAt;
}
