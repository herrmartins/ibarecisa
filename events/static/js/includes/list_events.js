let fetchEvents = async (page = 1) => {
    return await new Promise((resolve, reject) => {
        
        // TODO remover. dados apenas para teste
        const eventObject = {
            title: "Evento Hoje",
            id: "1",
            description: "Evento ocorre hoje",
            start_date: "01/01/2028 10:00:00",
            end_date: "05/01/2028 18:00:00",
            price: "150,00",
            category: "musica",
            location: {
                name: "Salão principal"
            },
            url_events_edit_event: "/events/edit/1",
        };

        // TODO remover. dados apenas para teste
        let dataFake = [
            [
                'Janeiro',
                [
                    eventObject,
                    eventObject,
                    eventObject,
                ]
            ],

            [
                'Fevereiro',
                [
                    eventObject,
                    eventObject,
                    eventObject,
                ]
            ]
        ];

        // TODO remover. Condicional apenas para teste
        if (page === 2) {
            dataFake = [
                [
                    'Março',
                    [
                        eventObject,
                        eventObject,
                        eventObject,
                    ]
                ] 
            ];
        }

        // TODO
        // fetch("/endpoint", {
        //     method: "GET",
        // })
        //     .then((response) => response.json())
        //     .then((result) => {
        //         resolve(result);
        //     })
        //     .catch((error) => {
        //         console.error(error);
        //     });
        
        resolve(dataFake);
    });
}

document.addEventListener('alpine:init', () => {   
    Alpine.store('allEvents', {
        page: 1,

        eventItems: [],

        seeMore() {
            this.page = ++this.page;

            (async () => {
                let data = await fetchEvents(this.page);

                this.eventItems = this.eventItems.concat(data);

                setTimeout(() => {
                    const element = document.getElementById("list-events");
            
                    element?.scrollIntoView({ behavior: "smooth", block: "end" });
                }, 250);
            })();
        },

        get dataEvents() {
            let data = this.eventItems;
            if (!this.eventItems.length) {
                data = async () => {
                    let data = await fetchEvents(this.page)
    
                    this.eventItems = this.eventItems.concat(data)

                    return this.eventItems;
                }
            }

            return data;
        }
    })
});