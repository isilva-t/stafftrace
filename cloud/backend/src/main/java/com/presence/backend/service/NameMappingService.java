package com.presence.backend.service;

import org.springframework.stereotype.Service;

@Service
public class NameMappingService {
	
	public String getDisplayName(String realName, 
							String fakeName,
							boolean isAuthenticated) {
		return isAuthenticated ? realName : fakeName;
	}
}
