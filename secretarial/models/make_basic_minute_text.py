from .date_utils import date_to_words


def make_minute(name_dict):
    text = [
        "Em reunião ordinária (ou extraordinária)",
        "meeting_date",
        "reuniram-se ",
        "number_of_atendees",
        " membros da ",
        "church",
        " sob a liderança do ",
        "presidente",
        ". Ele orou e declarou aberta a sessão. <p>O secretário ",
        "secretary",
        " leu a ata da reunião anterior. O irmão",
        "minute_reading_acceptance_proposal",
        " propôs a aceitação da ata lida e o irmão",
        "minute_reading_acceptance_proposal_support",
        " apoiou a proposta, havendo unanimidade por parte dos demais.</p> ",
        "<p>Houve leitura do relatório financeiro por ",
        "treasurer",
        ", com os seguintes valores: saldo anterior: R$",
        "last_months_balance",
        ", entradas: R$",
        "revenue",
        ", saídas: R$",
        "expenses",
        ". O irmão ",
        "finance_report_acceptance_proposal",
        " propôs a aceitação do relatório financeiro, recendo apoio do irmão ",
        "finance_report_acceptance_proposal_support",
        ". Houve unanimidade por parte dos demais.</p>",
        "<p>Não havendo assuntos em pauta, o pastor encerrou a sessão e eu ",
        "secretary",
        ", primeiro secretário,",
        "lavrei a presente ata que vai assinada por mim e pelo pastor.</p>",
        "meeting_date",
        "<p>", " Primeiro secretário:", "</p>",
        "<p>", "secretary", "</p>",
        "<p>", " Pastor:", "</p>",
        "<p>", "presidente", "</p>",
    ]
    result_text = []
    for word in text:
        if word in name_dict:
            if not word == "meeting_date":
                print("Não é meeting_date")
                result_text.append(str(name_dict[word]))
            else:
                result_text.append(date_to_words(name_dict[word]))
                print("É meeting_date")
        else:
            result_text.append(word)
    final_text = "".join(result_text)
    return final_text
