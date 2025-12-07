# Spring Boot Cloud Backend - Technical Specification

## Overview

The Spring Boot backend runs in the cloud (GKE) and is responsible for:
- Receiving heartbeat and hourly summary data from on-premise agents
- Storing aggregated data in MongoDB
- Providing REST API for Angular frontend
- Handling JWT authentication
- Managing name anonymization (real vs fake names)

---

## Project Structure

```
backend/
├── src/main/java/com/presence/
│   ├── PresenceApplication.java       # Main Spring Boot application
│   ├── config/
│   │   └── MongoConfig.java          # MongoDB configuration
│   ├── controller/
│   │   ├── AuthController.java       # Login endpoint
│   │   ├── HeartbeatController.java  # Receive heartbeats
│   │   └── PresenceController.java   # Presence data endpoints
│   ├── model/
│   │   ├── CurrentStatus.java        # MongoDB document
│   │   ├── DailyPresence.java        # MongoDB document
│   │   └── dto/                      # Data Transfer Objects
│   ├── repository/
│   │   ├── CurrentStatusRepository.java
│   │   └── DailyPresenceRepository.java
│   └── service/
│       ├── JwtService.java           # JWT token operations
│       ├── NameMappingService.java   # Real/fake name mapping
│       └── PresenceService.java      # Business logic
├── src/main/resources/
│   ├── application.properties        # Spring configuration
│   └── .env                          # Environment variables
├── pom.xml
└── Dockerfile
```

---

## MongoDB Collections

### CurrentStatus Collection
```javascript
{
  "_id": ObjectId("..."),
  "employeeId": 1,                    // User.id from Django
  "employeeName": "Ricardo_Silva",    // Real name
  "fakeName": "Employee_Alpha",       // Fake name
  "isPresent": true,
  "currentArea": "default",
  "lastSeen": ISODate("2024-12-06T16:45:23Z"),
  "updatedAt": ISODate("2024-12-06T16:45:23Z")
}
```

### DailyPresence Collection
```javascript
{
  "_id": ObjectId("..."),
  "employeeId": 1,
  "employeeName": "Ricardo_Silva",
  "fakeName": "Employee_Alpha",
  "date": "2024-12-06",               // Date only, no time
  "firstSeen": "08:47:00",            // Time only
  "lastSeen": "18:32:00",             // Time only
  "totalMinutes": 520,                // Sum of all hourly minutes
  "hoursPresent": 8.67,               // totalMinutes / 60
  "createdAt": ISODate("2024-12-06T09:00:00Z"),
  "updatedAt": ISODate("2024-12-06T19:00:00Z")
}
```

---

## Dependencies (pom.xml)

```xml
<dependencies>
    <!-- Spring Boot Starter -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    
    <!-- MongoDB -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-data-mongodb</artifactId>
    </dependency>
    
    <!-- JWT -->
    <dependency>
        <groupId>io.jsonwebtoken</groupId>
        <artifactId>jjwt-api</artifactId>
        <version>0.11.5</version>
    </dependency>
    <dependency>
        <groupId>io.jsonwebtoken</groupId>
        <artifactId>jjwt-impl</artifactId>
        <version>0.11.5</version>
        <scope>runtime</scope>
    </dependency>
    <dependency>
        <groupId>io.jsonwebtoken</groupId>
        <artifactId>jjwt-jackson</artifactId>
        <version>0.11.5</version>
        <scope>runtime</scope>
    </dependency>
    
    <!-- Lombok (optional, for cleaner code) -->
    <dependency>
        <groupId>org.projectlombok</groupId>
        <artifactId>lombok</artifactId>
        <optional>true</optional>
    </dependency>
</dependencies>
```

---

## MongoDB Models

### CurrentStatus.java
```java
package com.presence.model;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import java.time.LocalDateTime;

@Data
@Document(collection = "current_status")
public class CurrentStatus {
    @Id
    private String id;
    
    private Integer employeeId;
    private String employeeName;
    private String fakeName;
    private Boolean isPresent;
    private String currentArea;
    private LocalDateTime lastSeen;
    private LocalDateTime updatedAt;
}
```

### DailyPresence.java
```java
package com.presence.model;

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
```

---

## DTOs (Data Transfer Objects)

### HeartbeatRequest.java
```java
package com.presence.model.dto;

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
    }
}
```

### PresenceRequest.java
```java
package com.presence.model.dto;

import lombok.Data;
import java.util.List;

@Data
public class PresenceRequest {
    private String siteId;
    private String timestamp;
    private List<PresenceData> presenceData;
    
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
}
```

### EmployeeStatusDTO.java
```java
package com.presence.model.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@AllArgsConstructor
public class EmployeeStatusDTO {
    private Integer employeeId;
    private String employeeName;
    private Boolean isPresent;
    private String currentArea;
    private LocalDateTime lastSeen;
}
```

### LoginRequest.java
```java
package com.presence.model.dto;

import lombok.Data;

@Data
public class LoginRequest {
    private String username;
    private String password;
}
```

### LoginResponse.java
```java
package com.presence.model.dto;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class LoginResponse {
    private String token;
    private String message;
}
```

---

## JWT Service

```java
package com.presence.service;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.security.Keys;
import org.springframework.stereotype.Service;

import java.security.Key;
import java.util.Date;

@Service
public class JwtService {
    
    private final String SECRET_KEY = System.getenv("JWT_SECRET");
    private final long EXPIRATION_TIME = 86400000; // 24 hours
    
    private Key getSigningKey() {
        return Keys.hmacShaKeyFor(SECRET_KEY.getBytes());
    }
    
    public String generateToken(String username) {
        return Jwts.builder()
                .setSubject(username)
                .setIssuedAt(new Date())
                .setExpiration(new Date(System.currentTimeMillis() + EXPIRATION_TIME))
                .signWith(getSigningKey(), SignatureAlgorithm.HS256)
                .compact();
    }
    
    public boolean validateToken(String token) {
        try {
            Jwts.parserBuilder()
                    .setSigningKey(getSigningKey())
                    .build()
                    .parseClaimsJws(token);
            return true;
        } catch (Exception e) {
            return false;
        }
    }
    
    public String extractUsername(String token) {
        Claims claims = Jwts.parserBuilder()
                .setSigningKey(getSigningKey())
                .build()
                .parseClaimsJws(token)
                .getBody();
        return claims.getSubject();
    }
}
```

---

## Name Mapping Service

```java
package com.presence.service;

import org.springframework.stereotype.Service;

@Service
public class NameMappingService {
    
    public String getDisplayName(String realName, String fakeName, boolean isAuthenticated) {
        return isAuthenticated ? realName : fakeName;
    }
}
```

---

## Controllers

### AuthController.java
```java
package com.presence.controller;

import com.presence.model.dto.LoginRequest;
import com.presence.model.dto.LoginResponse;
import com.presence.service.JwtService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth")
@CrossOrigin(origins = "*")
public class AuthController {
    
    @Autowired
    private JwtService jwtService;
    
    private final String ADMIN_USERNAME = System.getenv("ADMIN_USERNAME");
    private final String ADMIN_PASSWORD = System.getenv("ADMIN_PASSWORD");
    
    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody LoginRequest request) {
        
        if (ADMIN_USERNAME.equals(request.getUsername()) && 
            ADMIN_PASSWORD.equals(request.getPassword())) {
            
            String token = jwtService.generateToken(request.getUsername());
            return ResponseEntity.ok(new LoginResponse(token, "Login successful"));
        }
        
        return ResponseEntity.status(401).body("Invalid credentials");
    }
}
```

### HeartbeatController.java
```java
package com.presence.controller;

import com.presence.model.CurrentStatus;
import com.presence.model.dto.HeartbeatRequest;
import com.presence.repository.CurrentStatusRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class HeartbeatController {
    
    @Autowired
    private CurrentStatusRepository currentStatusRepository;
    
    @PostMapping("/heartbeat")
    public ResponseEntity<String> receiveHeartbeat(@RequestBody HeartbeatRequest request) {
        
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime tenMinutesAgo = now.minusMinutes(10);
        
        // Mark devices in list as present
        for (HeartbeatRequest.DeviceOnline device : request.getDevicesOnline()) {
            CurrentStatus status = currentStatusRepository
                    .findByEmployeeId(device.getEmployeeId())
                    .orElse(new CurrentStatus());
            
            status.setEmployeeId(device.getEmployeeId());
            status.setEmployeeName(device.getEmployeeName());
            status.setFakeName(device.getFakeName());
            status.setIsPresent(true);
            status.setCurrentArea(device.getArea());
            status.setLastSeen(now);
            status.setUpdatedAt(now);
            
            currentStatusRepository.save(status);
        }
        
        // Mark devices not in list as absent (if not seen in 10 minutes)
        currentStatusRepository.findAll().forEach(status -> {
            boolean inCurrentList = request.getDevicesOnline().stream()
                    .anyMatch(d -> d.getEmployeeId().equals(status.getEmployeeId()));
            
            if (!inCurrentList && status.getLastSeen().isBefore(tenMinutesAgo)) {
                status.setIsPresent(false);
                status.setUpdatedAt(now);
                currentStatusRepository.save(status);
            }
        });
        
        return ResponseEntity.ok("Heartbeat received");
    }
}
```

### PresenceController.java
```java
package com.presence.controller;

import com.presence.model.CurrentStatus;
import com.presence.model.DailyPresence;
import com.presence.model.dto.*;
import com.presence.repository.CurrentStatusRepository;
import com.presence.repository.DailyPresenceRepository;
import com.presence.service.JwtService;
import com.presence.service.NameMappingService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class PresenceController {
    
    @Autowired
    private CurrentStatusRepository currentStatusRepository;
    
    @Autowired
    private DailyPresenceRepository dailyPresenceRepository;
    
    @Autowired
    private JwtService jwtService;
    
    @Autowired
    private NameMappingService nameMappingService;
    
    // POST endpoint to receive hourly summaries
    @PostMapping("/presence")
    public ResponseEntity<String> receivePresence(@RequestBody PresenceRequest request) {
        
        for (PresenceRequest.PresenceData data : request.getPresenceData()) {
            LocalDate date = LocalDate.parse(data.getDate());
            
            // Find or create daily presence record
            DailyPresence daily = dailyPresenceRepository
                    .findByEmployeeIdAndDate(data.getEmployeeId(), date)
                    .orElse(new DailyPresence());
            
            boolean isNew = daily.getId() == null;
            
            // Set basic fields
            daily.setEmployeeId(data.getEmployeeId());
            daily.setEmployeeName(data.getEmployeeName());
            daily.setFakeName(data.getFakeName());
            daily.setDate(date);
            
            // Update first_seen (keep earliest)
            LocalTime newFirstSeen = LocalTime.parse(data.getFirstSeen());
            if (isNew || daily.getFirstSeen() == null || newFirstSeen.isBefore(daily.getFirstSeen())) {
                daily.setFirstSeen(newFirstSeen);
            }
            
            // Update last_seen (keep latest)
            LocalTime newLastSeen = LocalTime.parse(data.getLastSeen());
            if (isNew || daily.getLastSeen() == null || newLastSeen.isAfter(daily.getLastSeen())) {
                daily.setLastSeen(newLastSeen);
            }
            
            // Add to total minutes
            int currentMinutes = daily.getTotalMinutes() != null ? daily.getTotalMinutes() : 0;
            daily.setTotalMinutes(currentMinutes + data.getMinutesOnline());
            daily.setHoursPresent(daily.getTotalMinutes() / 60.0);
            
            // Set timestamps
            if (isNew) {
                daily.setCreatedAt(LocalDateTime.now());
            }
            daily.setUpdatedAt(LocalDateTime.now());
            
            dailyPresenceRepository.save(daily);
        }
        
        return ResponseEntity.ok("Presence data received");
    }
    
    // GET current status
    @GetMapping("/current")
    public ResponseEntity<List<EmployeeStatusDTO>> getCurrentStatus(
            @RequestHeader(value = "Authorization", required = false) String authHeader) {
        
        boolean isAuthenticated = false;
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7);
            isAuthenticated = jwtService.validateToken(token);
        }
        
        List<CurrentStatus> statuses = currentStatusRepository.findAll();
        
        boolean finalIsAuthenticated = isAuthenticated;
        List<EmployeeStatusDTO> result = statuses.stream()
                .map(status -> new EmployeeStatusDTO(
                        status.getEmployeeId(),
                        nameMappingService.getDisplayName(
                                status.getEmployeeName(),
                                status.getFakeName(),
                                finalIsAuthenticated
                        ),
                        status.getIsPresent(),
                        status.getCurrentArea(),
                        status.getLastSeen()
                ))
                .collect(Collectors.toList());
        
        return ResponseEntity.ok(result);
    }
    
    // GET daily report
    @GetMapping("/daily")
    public ResponseEntity<List<DailyPresence>> getDailyReport(
            @RequestParam String date,
            @RequestHeader(value = "Authorization", required = false) String authHeader) {
        
        boolean isAuthenticated = false;
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7);
            isAuthenticated = jwtService.validateToken(token);
        }
        
        LocalDate queryDate = LocalDate.parse(date);
        List<DailyPresence> records = dailyPresenceRepository.findByDate(queryDate);
        
        // Apply name mapping
        boolean finalIsAuthenticated = isAuthenticated;
        records.forEach(record -> {
            String displayName = nameMappingService.getDisplayName(
                    record.getEmployeeName(),
                    record.getFakeName(),
                    finalIsAuthenticated
            );
            record.setEmployeeName(displayName);
        });
        
        return ResponseEntity.ok(records);
    }
    
    // GET monthly summary
    @GetMapping("/monthly")
    public ResponseEntity<List<MonthlyPresenceDTO>> getMonthlyReport(
            @RequestParam int year,
            @RequestParam int month,
            @RequestHeader(value = "Authorization", required = false) String authHeader) {
        
        boolean isAuthenticated = false;
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7);
            isAuthenticated = jwtService.validateToken(token);
        }
        
        LocalDate startDate = LocalDate.of(year, month, 1);
        LocalDate endDate = startDate.plusMonths(1).minusDays(1);
        
        List<DailyPresence> records = dailyPresenceRepository
                .findByDateBetween(startDate, endDate);
        
        // Group by employee and calculate totals
        // ... (aggregation logic)
        
        return ResponseEntity.ok(null); // Implement aggregation
    }
    
    // GET employee monthly detail
    @GetMapping("/employee/{employeeId}/monthly")
    public ResponseEntity<EmployeeMonthlyDetailDTO> getEmployeeMonthlyDetail(
            @PathVariable Integer employeeId,
            @RequestParam int year,
            @RequestParam int month,
            @RequestHeader(value = "Authorization", required = false) String authHeader) {
        
        boolean isAuthenticated = false;
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7);
            isAuthenticated = jwtService.validateToken(token);
        }
        
        LocalDate startDate = LocalDate.of(year, month, 1);
        LocalDate endDate = startDate.plusMonths(1).minusDays(1);
        
        List<DailyPresence> records = dailyPresenceRepository
                .findByEmployeeIdAndDateBetween(employeeId, startDate, endDate);
        
        // Build response with all days of month
        // ... (implementation)
        
        return ResponseEntity.ok(null); // Implement detail view
    }
}
```

---

## Repositories

### CurrentStatusRepository.java
```java
package com.presence.repository;

import com.presence.model.CurrentStatus;
import org.springframework.data.mongodb.repository.MongoRepository;
import java.util.Optional;

public interface CurrentStatusRepository extends MongoRepository<CurrentStatus, String> {
    Optional<CurrentStatus> findByEmployeeId(Integer employeeId);
}
```

### DailyPresenceRepository.java
```java
package com.presence.repository;

import com.presence.model.DailyPresence;
import org.springframework.data.mongodb.repository.MongoRepository;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

public interface DailyPresenceRepository extends MongoRepository<DailyPresence, String> {
    Optional<DailyPresence> findByEmployeeIdAndDate(Integer employeeId, LocalDate date);
    List<DailyPresence> findByDate(LocalDate date);
    List<DailyPresence> findByDateBetween(LocalDate startDate, LocalDate endDate);
    List<DailyPresence> findByEmployeeIdAndDateBetween(Integer employeeId, LocalDate startDate, LocalDate endDate);
}
```

---

## Configuration

### application.properties
```properties
# Server
server.port=8080

# MongoDB
spring.data.mongodb.uri=${MONGODB_URI}
spring.data.mongodb.database=presence_monitor

# CORS (for development)
spring.web.cors.allowed-origins=*
spring.web.cors.allowed-methods=GET,POST,PUT,DELETE,OPTIONS
spring.web.cors.allowed-headers=*
```

### .env
```bash
# MongoDB
MONGODB_URI=mongodb://localhost:27017/presence_monitor

# JWT
JWT_SECRET=your-super-secret-key-min-256-bits-long-change-this

# Admin credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=demo123
```

---

## Running Locally

```bash
# Start MongoDB
docker run -d -p 27017:27017 --name mongodb mongo:7

# Run Spring Boot
./mvnw spring-boot:run

# Or with Maven wrapper
mvn spring-boot:run
```

Access API at: `http://localhost:8080`

---

## API Endpoints Summary

| Method | Endpoint | Auth Required | Purpose |
|--------|----------|---------------|---------|
| POST | `/api/auth/login` | No | Get JWT token |
| POST | `/api/heartbeat` | No | Receive device status |
| POST | `/api/presence` | No | Receive hourly summaries |
| GET | `/api/current` | Optional | Current status (real/fake names) |
| GET | `/api/daily?date=YYYY-MM-DD` | Optional | Daily report |
| GET | `/api/monthly?year=YYYY&month=MM` | Optional | Monthly summary |
| GET | `/api/employee/{id}/monthly?year=YYYY&month=MM` | Optional | Employee detail |

---

## Related Documents
- [01-system-architecture.md](./01-system-architecture.md) - System overview
- [02-django-agent.md](./02-django-agent.md) - On-premise agent
- [04-angular-frontend.md](./04-angular-frontend.md) - Frontend implementation
- [05-deployment.md](./05-deployment.md) - Deployment guide
