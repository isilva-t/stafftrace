package com.presence.backend.repository;

import com.presence.backend.model.AgentDowntime;
import org.springframework.data.mongodb.repository.MongoRepository;
import java.time.LocalDateTime;
import java.util.List;

public interface AgentDowntimeRepository extends MongoRepository<AgentDowntime, String> {
	List<AgentDowntime> findByDowntimeStartBetween(LocalDateTime start, LocalDateTime end);
}
