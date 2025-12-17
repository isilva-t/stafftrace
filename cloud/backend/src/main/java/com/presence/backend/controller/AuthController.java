package com.presence.backend.controller;

import com.presence.backend.model.dto.LoginRequest;
import com.presence.backend.model.dto.LoginResponse;
import com.presence.backend.service.JwtService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import com.presence.backend.service.LoginRateLimiter;

@RestController
@RequestMapping("/api/auth")
@CrossOrigin(origins = "*")
public class AuthController {

	@Autowired
	private JwtService jwtService;

	@Autowired
	private LoginRateLimiter loginRateLimiter;

	private final String ADMIN_USERNAME = System.getenv("ADMIN_USERNAME");
	private final String ADMIN_PASSWORD = System.getenv("ADMIN_PASSWORD");

	@PostMapping("/login")
	public ResponseEntity<?> login(@RequestBody LoginRequest request) {

		if (loginRateLimiter.isLockedOut()) {
			long minutesRemaining = loginRateLimiter.getMinutesRemaining();
			String message = "Too many failed attempts. Try again in " +
					minutesRemaining + " minutes.";
			return ResponseEntity.status(429).body(message);
		}

		if (ADMIN_USERNAME.equals(request.getUsername()) &&
				ADMIN_PASSWORD.equals(request.getPassword())) {

			loginRateLimiter.reset();
			String token = jwtService.generateToken(request.getUsername());
			return ResponseEntity.ok(new LoginResponse(token, "Login successful"));
		}

		loginRateLimiter.recordFailure();
		return ResponseEntity.status(401).body("Invalid credentials");
	}
}
