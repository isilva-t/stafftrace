package com.presence.backend.service;

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
	private final long EXPIRATION_TIME = 86400000; //24 hours

	private key getSigningKey() {
		return Keys.hmacShaKeyFor(SECRET_KEY.getBytes());
	}

	public String generateToken(String username) {
		return Jwts.builder()
				.setSubject(username)
				.setIssueAt(new Date())
				.setExpiration(new Date(System.currentTimeMillies() + EXPIRATION_TIME))
				.signWith(getSigningKey(), SignatureAlgorithm.HS256)
				.compact();
	}

	public boolean validateToken(String token) {
		try {
			Jwts.parseBuilder()
				.SetSigningKey(getSigningKey())
				.build()
				.parseClaimsJws(token);
			return true;
			} catch (Exception e) {
				return false;
			}
		}
	}

	public String extractUsername(String token) {
		Claims claims = Jwts.parseBuilder()
			.setSigningKey(getSigningKey())
			.build()
			.parseClaimsJws(token)
			.getBody();
		return claims.getSubject();
	}
}
