package com.presence.backend.repository;

import com.presence.backend.model.DailyPresence;
import org.springframework.data.mongodb.repository.MongoRepository;
import java.time.LocalDate;
import java.time.LocalTime;
import java.util.List;
import java.util.Optional;

public interface DailyPresenceRepository extends MongoRepository<DailyPresence, String> {
	Optional<DailyPresence> findByEmployeeIdAndDate(Integer employeeId, LocalDate date);
	List<DailyPresence> findByDate(LocalDate date);
	List<DailyPresence> findByDateBetween(LocalDate startDate, LocalDate endDate);
	List<DailyPresence> findByEmployeeIdAndDateBetween(Integer employeeId, LocalDate startDate, LocalDate endDate);
}
