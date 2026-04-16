"""
Tests for the Mergington High School Activities API
"""

import pytest
from urllib.parse import quote


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirect(self, client):
        """Test that root redirects to static HTML"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the /activities endpoint"""

    def test_get_all_activities(self, client, reset_activities):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        assert "Basketball" in data
        assert "Tennis" in data
        assert "Art Club" in data
        assert "Music Ensemble" in data
        assert "Science Olympiad" in data
        assert "Debate Team" in data

    def test_activity_structure(self, client, reset_activities):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)

    def test_activities_participants(self, client, reset_activities):
        """Test that activities contain initial participants"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignup:
    """Tests for the /activities/{activity_name}/signup endpoint"""

    def test_successful_signup(self, client, reset_activities):
        """Test successfully signing up for an activity"""
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity]["participants"]

    def test_signup_duplicate_email(self, client, reset_activities):
        """Test that duplicate signups are rejected"""
        email = "michael@mergington.edu"  # Already signed up for Chess Club
        activity = "Chess Club"
        
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signup for non-existent activity"""
        email = "student@mergington.edu"
        activity = "Nonexistent Activity"
        
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_multiple_students(self, client, reset_activities):
        """Test multiple students signing up for different activities"""
        emails = [
            "alice@mergington.edu",
            "bob@mergington.edu",
            "charlie@mergington.edu"
        ]
        activity = "Programming Class"
        
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all were added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        for email in emails:
            assert email in activities_data[activity]["participants"]

    def test_signup_special_characters_in_email(self, client, reset_activities):
        """Test signup with special characters in email"""
        email = "student+tag@mergington.edu"
        activity = "Art Club"
        
        response = client.post(
            f"/activities/{activity}/signup?email={quote(email)}"
        )
        
        assert response.status_code == 200
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity]["participants"]


class TestUnregister:
    """Tests for the /activities/{activity_name}/unregister endpoint"""

    def test_successful_unregister(self, client, reset_activities):
        """Test successfully unregistering from an activity"""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Verify initial state
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data[activity]["participants"]

    def test_unregister_not_signed_up(self, client, reset_activities):
        """Test unregistering a student not signed up for activity"""
        email = "notstudent@mergington.edu"
        activity = "Chess Club"
        
        response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregister from non-existent activity"""
        email = "student@mergington.edu"
        activity = "Nonexistent Activity"
        
        response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_unregister_then_resign_up(self, client, reset_activities):
        """Test that student can re-sign up after unregistering"""
        email = "testuser@mergington.edu"
        activity = "Basketball"
        
        # Sign up
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Unregister
        response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Sign up again
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify they're signed up
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity]["participants"]

    def test_unregister_multiple_students(self, client, reset_activities):
        """Test unregistering multiple students"""
        activity = "Art Club"
        
        # Get initial participants
        response = client.get("/activities")
        initial_participants = response.json()[activity]["participants"][:]
        
        # Unregister first participant
        for email in initial_participants:
            response = client.post(
                f"/activities/{activity}/unregister?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all were removed
        activities_response = client.get("/activities")
        assert len(activities_response.json()[activity]["participants"]) == 0


class TestIntegration:
    """Integration tests for complex scenarios"""

    def test_full_signup_unregister_flow(self, client, reset_activities):
        """Test complete signup and unregister flow"""
        email = "integration@mergington.edu"
        activity = "Science Olympiad"
        
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])
        
        # Sign up
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify count increased
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_count + 1
        
        # Unregister
        response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Verify count decreased
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_count

    def test_availability_updates_after_signup(self, client, reset_activities):
        """Test that availability updates correctly after signup"""
        activity = "Tennis"
        email = "newplayer@mergington.edu"
        
        # Get initial availability
        response = client.get("/activities")
        initial_data = response.json()[activity]
        initial_available = initial_data["max_participants"] - len(initial_data["participants"])
        
        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Check new availability
        response = client.get("/activities")
        new_data = response.json()[activity]
        new_available = new_data["max_participants"] - len(new_data["participants"])
        
        assert new_available == initial_available - 1

    def test_concurrent_operations(self, client, reset_activities):
        """Test multiple operations in sequence"""
        activity = "Debate Team"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        # Sign up multiple students
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Unregister middle student
        response = client.post(
            f"/activities/{activity}/unregister?email={emails[1]}"
        )
        assert response.status_code == 200
        
        # Verify state
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        assert emails[0] in participants
        assert emails[1] not in participants
        assert emails[2] in participants
