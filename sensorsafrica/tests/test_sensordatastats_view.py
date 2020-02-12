import datetime

import pytest
from django.utils import timezone
import dateutil.parser


@pytest.mark.django_db
class TestGettingData:
    def test_getting_air_data_now(self, client, modified_datavalues):
        response = client.get(
            "/v2/data/air/?city=Dar es Salaam", format="json")
        assert response.status_code == 200

        data = response.json()

        assert data["count"] == 1

        result = data["results"][0]

        assert "P1" in result
        assert result["P1"]["average"] == 0.0
        assert result["P1"]["maximum"] == 0.0
        assert result["P1"]["minimum"] == 0.0

        assert "P2" in result

        # One node has an average of 5.5 for sample size 6
        # Another node has an average of 0 for sample size 6
        # The average for the city will be (5.5 * 6 + 0 * 6) / (6 + 6) = 2.75
        assert result["P2"]["average"] == 2.75

        assert result["P2"]["maximum"] == 8.0
        assert result["P2"]["minimum"] == 0.0

    def test_getting_air_data_now_all_cities(self, client, modified_datavalues):
        response = client.get("/v2/data/air/", format="json")
        assert response.status_code == 200

        data = response.json()

        assert data["count"] == 3

        results = data["results"]

        assert results[0]["city_name"] == "Bagamoyo"
        assert results[1]["city_name"] == "Dar es Salaam"
        assert "P1" in results[1]
        assert results[1]["city_name"] == "Dar es Salaam"
        assert "P2" in results[1]
        assert results[2]["city_name"] == "Nairobi"

    def test_getting_air_data_now_filter_cities(self, client, modified_datavalues):
        response = client.get(
            "/v2/data/air/?city=Dar es Salaam,Bagamoyo", format="json"
        )
        assert response.status_code == 200

        data = response.json()

        assert data["count"] == 2

        results = data["results"]

        assert results[0]["city_name"] == "Bagamoyo"
        assert results[1]["city_name"] == "Dar es Salaam"
        assert "P1" in results[1]
        assert results[1]["city_name"] == "Dar es Salaam"
        assert "P2" in results[1]

    def test_getting_air_data_value_type(self, client, modified_datavalues):
        response = client.get(
            "/v2/data/air/?city=Dar es Salaam&value_type=P2", format="json"
        )
        assert response.status_code == 200

        data = response.json()

        assert data["count"] == 1
        assert "P2" in data["results"][0]
        assert "P1" not in data["results"][0]
        assert "temperature" not in data["results"][0]
        assert "humidity" not in data["results"][0]

    def test_getting_air_data_from_date(self, client, modified_datavalues):
        response = client.get(
            "/v2/data/air/?city=Dar es Salaam&from=%s"
            % (timezone.now() - datetime.timedelta(days=2)).date(),
            format="json",
        )
        assert response.status_code == 200

        data = response.json()

        assert type(data["results"][0]["P2"]) == list

        # Data is in descending order by date
        most_recent_value = data["results"][0]["P2"][0]
        most_recent_date = dateutil.parser.parse(most_recent_value["end_datetime"])

        # Check today is not included
        assert most_recent_date.date() < datetime.datetime.today().date()

    def test_getting_air_data_from_date_to_date(self, client, modified_datavalues):
        now = timezone.now()
        response = client.get(
            "/v2/data/air/?city=Dar es Salaam&from=%s&to=%s" % (
                now.date(), now.date()),
            format="json",
        )
        assert response.status_code == 200

        data = response.json()

        assert data["count"] == 1
        assert type(data["results"][0]["P1"]) == list
        assert type(data["results"][0]["P2"]) == list

    def test_getting_air_data_with_invalid_request(self, client, modified_datavalues):
        response = client.get(
            "/v2/data/air/?city=Dar es Salaam&to=2019-02-08", format="json"
        )
        assert response.status_code == 400
        assert response.json() == {
            "from": "Must be provide along with to query"}

    def test_getting_air_data_with_invalid_from_request(self, client, modified_datavalues):
        response = client.get(
            "/v2/data/air/?city=Dar es Salaam&from=2019-23-08", format="json"
        )
        assert response.status_code == 400
        assert response.json() == {
            "from": "Must be a date in the format Y-m-d."}

    def test_getting_air_data_with_invalid_to_request(self, client, modified_datavalues):
        response = client.get(
            "/v2/data/air/?city=Dar es Salaam&from=2019-02-08&to=08-02-2019",
            format="json",
        )
        assert response.status_code == 400
        assert response.json() == {"to": "Must be a date in the format Y-m-d."}

    def test_getting_air_data_now_with_additional_values(
        self, client, additional_sensorsdatastats
    ):
        response = client.get(
            "/v2/data/air/?city=Dar es Salaam", format="json")
        assert response.status_code == 200

        data = response.json()

        assert data["count"] == 1

        result = data["results"][0]

        assert "P1" in result
        assert result["P1"]["average"] == 0.0
        assert result["P1"]["maximum"] == 0.0
        assert result["P1"]["minimum"] == 0.0

        assert "P2" in result

        # The previous average was 2.75 for sample size 12
        # The addional data average is 4 for sample size 3
        # The new average is (2.75 * 12 + 4 * 3) / (12 + 3) = 3
        assert result["P2"]["average"] == 3

        assert result["P2"]["maximum"] == 8.0
        assert result["P2"]["minimum"] == 0.0

    def test_geting_air_data_by_the_hour(self, client, modified_datavalues):
        now = timezone.now()
        response = client.get(
            "/v2/data/air/?city=Dar es Salaam&avg=hour&from=%s&to=%s" % (
                now.date(), now.date()),
            format="json",
        )
        assert response.status_code == 200

        data = response.json()

        assert data["count"] == 1
        assert type(data["results"][0]["P1"]) == list
        assert type(data["results"][0]["P2"]) == list

        assert len(data["results"][0]["P1"]) == 1
        assert len(data["results"][0]["P2"]) == 4

    def test_geting_air_data_by_the_month(self, client, modified_datavalues):
        now = timezone.now()
        response = client.get(
            "/v2/data/air/?city=Dar es Salaam&avg=month&from=%s&to=%s" % (
                now.date(), now.date()),
            format="json",
        )
        assert response.status_code == 200

        data = response.json()

        assert data["count"] == 1
        assert type(data["results"][0]["P1"]) == list
        assert type(data["results"][0]["P2"]) == list

        assert len(data["results"][0]["P1"]) == 1
        assert len(data["results"][0]["P2"]) == 1

    def test_geting_air_data_by_the_minute(self, client, modified_datavalues):
        now = timezone.now()
        response = client.get(
            "/v2/data/air/?city=Dar es Salaam&avg=minute&from=%s&to=%s" % (
                now.date(), now.date()),
            format="json",
        )
        assert response.status_code == 200

        data = response.json()

        assert data["count"] == 1
        assert type(data["results"][0]["P1"]) == list
        assert type(data["results"][0]["P2"]) == list

        assert len(data["results"][0]["P1"]) == 1
        assert len(data["results"][0]["P2"]) == 4
