package com.presence.backend.model;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import java.time.LocalDateTime;

@Data
@Document(collection = "current_status")
public class CurrentStatus {
	@Id
	private String id;

	private Integer			employeeId;
	private String			employeeName;
	private String			fakeName;
	private Boolean			isPresent;
	private String			currentArea;
	private LocalDateTime	lastSeen;
	private	LocalDateTime	updatedAt;
}
