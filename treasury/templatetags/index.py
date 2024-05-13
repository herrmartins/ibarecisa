from django import template

register = template.Library()
# É uma custom tag para usar dentro do template do django
# No relatório mensal, há o loop para colocar as linhas da tabela
# Mas não tinha fazer o subtotal, o que foi feito na view
# Não tinha como acessar os valores do subtotal, senão com um loop
# Esse filtro faz um contador para pegar os valores da lista do subtotal


@register.filter
def index(sequence, position):
    return sequence[position]
