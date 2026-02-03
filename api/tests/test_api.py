from rest_framework.test import APITestCase
from django.urls import reverse
from secretarial.models import MinuteExcerptsModel
from users.models import CustomUser
from model_bakery import baker
from rest_framework import status


class TestViews(APITestCase):
    """
    Testes para a API secretarial (atas, excertos, busca).

    Nota: Os testes da antiga API de tesouraria foram removidos
    pois a nova tesouraria usa DRF ViewSets em /treasury/api/.
    """

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        baker.make("CustomUser", first_name="Mary",
                   type=CustomUser.Types.REGULAR)
        baker.make("secretarial.MinuteTemplateModel", body="Lorem ipsum...")
        baker.make("secretarial.MeetingMinuteModel", body="Lorem ipsum...")

    def test_get_data(self):
        MinuteExcerptsModel.objects.create()

        url = reverse("get-data")
        self.client.force_login(self.user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_detailed_data(self):
        minute_excerpt = baker.make(MinuteExcerptsModel)
        pk = 1
        url = reverse("get-detailed-data", kwargs={"pk": pk})
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unified_search(self):
        self.client.force_login(self.user)
        url = reverse("secretarial-search")
        user_data = {"category": "users", "searched": "John Doe"}
        response = self.client.post(url, user_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        member_data = {"category": "members", "searched": "Rafael"}
        response = self.client.post(url, member_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        min_template_data = {"category": "templates", "searched": "Lorem"}
        response = self.client.post(url, min_template_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        minute_data = {"category": "minutes", "searched": "Lorem"}
        response = self.client.post(url, minute_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        invalid_data = {"category": "invalid", "searched": "Lorem"}
        response = self.client.post(url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
