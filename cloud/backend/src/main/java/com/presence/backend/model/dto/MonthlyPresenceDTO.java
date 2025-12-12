package com.presence.backend.model.dto;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class MonthlyPresenceDTO {
	private Integer employeeId;
	private String employeeName;
	private Double totalHours;
	private Integer daysPresent;
	private Double avgHoursPerDay;
}
