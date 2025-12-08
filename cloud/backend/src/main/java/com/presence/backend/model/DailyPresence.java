package com.presence.backend.model;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.CompoundIndex;
import org.springframework.data.mongodb.core.mapping.Document;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;

@Data
@Document(collection = "daily_presence")
@CompoundIndex(name = "employee_date_idx", def = "{'employeeId': 1, 'date': 1}", unique = true)
public class DailyPresence {
	@Id
	private String id;

	private Integer employeeId;
	private String employeeName;
	private String fakeName;
	private LocalDate date;
	private LocalTime firstSeen;
	private LocalTime lastSeen;
	private Integer totalMinutes;
	private Double hoursPresent;
	private LocalDateTime createdAt;
	private LocalDateTime updatedAt;
}
