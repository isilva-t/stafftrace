package com.presence.backend.model.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@AllArgsConstructor
public class EmployeeStatusDTO {
	private Integer	employeeId;
	private String	employeeName;
	private Boolean	isPresent;
	private String	CurrentArea;
	private LocalDateTime	lastSeen;
}
