package com.presence.backend.model.dto;

import lombok.Data;
import java.util.List;

@Data
public class HeartbeatRequest {
	private String siteId;
	private String timestamp;
	private List<DeviceOnline> devicesOnline;

	@Data
	public static class DeviceOnline {
		private Integer employeeId;
		private String employeeName;
		private String fakeName;
		private String area;
		private Boolean isPresent;
	}
}
