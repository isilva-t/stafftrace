package com.presence.backend.repository;

import com.presence.backend.model.AgentHealth;
import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.Optional;

public interface AgentHealthRepository extends MongoRepository<AgentHealth, String> {
	Optional<AgentHealth> findBySiteId(String site_id);
}
