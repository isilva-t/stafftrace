package com.presence.backend.model.dto;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class DailyDetailDTO {
	private String date;
	private String dayOfWeek;
	private String firstSeen;
	private String lastSeen;
	private Double hours;
	private String status;
}
