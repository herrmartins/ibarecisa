import unittest
from secretarial.utils.make_basic_minute_text import make_minute


class TestMakeMinute(unittest.TestCase):
    def test_make_minute(self):
        self.maxDiff = None
        name_dict = {
            "meeting_date": "2023-12-31",
            "number_of_attendees": 10,
            "church": "Sample Church",
            "presidente": "president",
            "secretary": "Sample Secretary",
            "minute_reading_acceptance_proposal": "Sample Minute Reading Acceptance Proposal",
            "minute_reading_acceptance_proposal_support": "Supporting Member",
            "treasurer": "Sample Treasurer",
            "last_months_balance": 1000,
            "revenue": 500,
            "expenses": 300,
            "finance_report_acceptance_proposal": "Sample Finance Report Acceptance Proposal",
            "finance_report_acceptance_proposal_support": "Supporting Member",
        }

        expected_output = (
            "Em 31 de dezembro de 2023, reuniram-se 10 membros da Sample Church "
            "sob a liderança do Pr. president. Ele orou e declarou aberta a sessão. "
            "<p>O secretário Sample Secretary leu a ata da reunião anterior. "
            "Sample Minute Reading Acceptance Proposal propôs a aceitação da ata lida "
            "e Supporting Member apoiou a proposta, havendo unanimidade por parte dos demais.</p> "
            "<p>Houve leitura do relatório financeiro por Sample Treasurer, com os seguintes valores: "
            "saldo anterior: R$1000, entradas: R$500, saídas: R$300. "
            "Sample Finance Report Acceptance Proposal propôs a aceitação do relatório financeiro, "
            "recendo apoio de Supporting Member. Houve unanimidade por parte dos demais.</p>"
            "<p>Não havendo assuntos em pauta, o pastor encerrou a sessão e eu Sample Secretary, "
            "primeiro secretário, lavrei a presente ata que vai assinada por mim e pelo pastor.</p>"
            "31 de dezembro de 2023, <p> Primeiro secretário:</p><p>Sample Secretary</p>"
            "<p> Pastor:</p><p>president</p>"
        )

        actual_output = make_minute(name_dict)
        self.assertEqual(actual_output, expected_output)


if __name__ == "__main__":
    unittest.main()
