let fetchEvents = async () => {
    return await new Promise((resolve, reject) => {
        // TODO - pegar os valores dinâmico de período 
        fetch("/events/byperiod?start_date=2024-07-23&end_date=2024-07-25", {
            method: "GET",
        })
            .then((response) => response.json())
            .then((result) => {                
                resolve(result.events);
            })
            .catch((error) => {
                console.error(error);
            });
    });
}

document.addEventListener('alpine:init', () => {   
    Alpine.store('allEvents', {
        eventItems: [],

        canYouMakeTheFirstCall: true,

        seeMore() {
            (async () => {
                let data = await fetchEvents();

                this.eventItems = this.eventItems.concat(data);

                setTimeout(() => {
                    const element = document.getElementById("list-events");
            
                    element?.scrollIntoView({ behavior: "smooth", block: "end" });
                }, 250);
            })();
        },

        set dataEvents (eventDate) {
            // TODO
            console.log(eventDate);
        },

        get dataEvents() {
            if (this.canYouMakeTheFirstCall) {
                (async () => {
                    let data = await fetchEvents();

                    this.eventItems = this.eventItems.concat(data);                    
                    
                    this.canYouMakeTheFirstCall = false;
                })();
            }

            return this.eventItems;
        }
    })
});