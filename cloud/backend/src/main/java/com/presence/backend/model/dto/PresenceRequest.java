package com.presence.backend.model.dto;

import lombok.Data;
import java.util.List;

@Data
public class PresenceRequest {
	private String siteId;
	private String timestamp;
	private List<PresenceData> presenceData;
	private List<AgentDowntimeData> agentDowntimes;

	@Data
	public static class PresenceData {
		private Integer employeeId;
		private String employeeName;
		private String fakeName;
		private String date;
		private Integer hour;
		private String firstSeen;
		private String lastSeen;
		private Integer minutesOnline;
	}

	@Data
	public static class AgentDowntimeData {
		private String downtimeStart;
		private String downtimeEnd;
	}
}
