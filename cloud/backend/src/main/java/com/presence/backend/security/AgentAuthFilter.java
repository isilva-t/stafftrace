package com.presence.backend.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Component
public class AgentAuthFilter extends OncePerRequestFilter {

	@Value("${agent.auth.token}")
	private String agentAuthToken;

	@Override
	protected void doFilterInternal(HttpServletRequest request,
			HttpServletResponse response,
			FilterChain filterChain) throws ServletException, IOException {

		String path = request.getRequestURI();

		if (path.startsWith("/api/heartbeat") || path.startsWith("/api/presence")) {
			String authHeader = request.getHeader("Authorization");

			if (authHeader == null || !authHeader.startsWith("Bearer ")) {
				response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
				response.getWriter().write("Unauthorized: Missing token");
				return;
			}

			String token = authHeader.substring(7); // remove bearer
			if (!token.equals(agentAuthToken)) {
				response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
				response.getWriter().write("Unauthorized: Invalid token");
				return;
			}
		}
		filterChain.doFilter(request, response);
	}
}
