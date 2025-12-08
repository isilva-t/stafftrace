package com.presence.backend.repository;

import com.presence.backend.model.CurrentStatus;

import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.Optional;

public interface CurrentStatusRepository extends MongoRepository<CurrentStatus, String> {
	Optional<CurrentStatus> findByEmployeeId(Integer employeeId);
}
