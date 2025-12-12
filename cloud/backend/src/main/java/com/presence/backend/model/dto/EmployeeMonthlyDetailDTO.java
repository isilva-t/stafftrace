package com.presence.backend.model.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import java.util.List;

@Data
@AllArgsConstructor
public class EmployeeMonthlyDetailDTO {
	private Integer employeeId;
	private String employeeName;
	private Integer year;
	private Integer month;
	private List<DailyDetailDTO> dailyRecords;
	private Double totalHours;
	private Integer daysPresent;
}
