/*global HikePlannerApp _config*/

var HikePlannerApp = window.HikePlannerApp || {};

(function planScopeWrapper($) {
    var authToken;
    HikePlannerApp.authToken.then(function setAuthToken(token) {
        if (token) {
            authToken = token;
        } else {
            window.location.href = '/login.html';
        }
    }).catch(function handleTokenError(error) {
        alert(error);
        window.location.href = '/login.html';
    });
    function planHike(trailId, startDate) {
        $.ajax({
            method: 'POST',
            url: _config.api.invokeUrl + '/gethikedata',
            headers: {
                Authorization: authToken
            },
            data: JSON.stringify({
                StartDate: startDate,
                TrailId: trailId,
                Username: HikePlannerApp.currentUser.username
            }),
            contentType: 'application/json',
            success: formSubmitted
        });
    }

    // if the user submits the form, send an API request
    $(function onDocReady() {
        $("#plannerForm").on('submit', handleFormSubmit);
    });

    function handleFormSubmit(event) {
        event.preventDefault();
        var trailName = document.getElementById("hikeLocationInput").value;
        var trailId = getTrailId(trailName);
        var startDate = document.getElementById("hikeDateInput").value;
        planHike(trailId, startDate);
    }

    // alert user of completion, reload the page
    function formSubmitted(event) {
        alert("Hike planned successfully! Check your email for plan details");
        window.location.href = '/planner.html';
    }

    // get the trail id
    function getTrailId(trailName) {
        switch (trailName) {
            case "Tuckerman's Ravine":
                return "7006930";
            case "Mt. Chocorua":
                return "7010621";
            case "Mt. Kinsman":
                return "7018513";
            case "Mount Pemigewasset Trail":
                return "7044100";
        }
    }

}(jQuery));




