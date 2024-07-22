let fetchEvents = async () => {
    return await new Promise((resolve, reject) => {
        const eventObject = {
            title: "Evento Hoje",
            id: "1",
            description: "Evento ocorre hoje",
            start_date: "01/01/2028 10:00:00",
            end_date: "05/01/2028 18:00:00",
            price: "15000",
            category: "musica",
            location: {
                name: "Salão principal"
            }
        };

        const data = [
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
        
        resolve(data);
    });
}