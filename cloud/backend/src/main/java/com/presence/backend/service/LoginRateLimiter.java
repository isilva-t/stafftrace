package com.presence.backend.service;

import org.springframework.stereotype.Service;
import java.time.LocalDateTime;
import java.util.concurrent.atomic.AtomicInteger;

@Service
public class LoginRateLimiter {

	private static final int MAX_ATTEMPTS = 5;
	private static final int LOCKOUT_MINUTES = 15;

	private final AtomicInteger failedAttempts = new AtomicInteger(0);
	private LocalDateTime lockoutUntil = null;

	public boolean isLockedOut() {
		if (lockoutUntil == null) {
			return false;
		}

		if (LocalDateTime.now().isBefore(lockoutUntil)) {
			return true;
		}

		reset();
		return false;
	}

	public long getMinutesRemaining() {
		if (lockoutUntil == null) {
			return 0;
		}
		long minutes = java.time.Duration.between(
				LocalDateTime.now(),
				lockoutUntil).toMinutes();

		return Math.max(0, minutes);
	}

	public void recordFailure() {
		int attempts = failedAttempts.incrementAndGet();

		if (attempts >= MAX_ATTEMPTS) {
			lockoutUntil = LocalDateTime.now().plusMinutes(LOCKOUT_MINUTES);
			System.out.println("🔒 Login locked for " + LOCKOUT_MINUTES + " minutes");
		}
	}

	public void reset() {
		failedAttempts.set(0);
		lockoutUntil = null;
	}
}
