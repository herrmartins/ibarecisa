const defaultDates = () => {
    let currentDate = new Date();
    const defaultStartDate = currentDate.toISOString().split('T')[0];
    document.querySelector("#start_date").valueAsDate = currentDate;

    currentDate.setMonth(currentDate.getMonth() + 1)
    document.querySelector("#end_date").valueAsDate = currentDate;
    const defaultEndDate = currentDate.toISOString().split('T')[0];

    return {
        defaultStartDate,
        defaultEndDate,
    };
};

let fetchEvents = async (startDate, endDate) => {

    if (!(startDate && endDate)) {
        const {defaultStartDate, defaultEndDate} = defaultDates();
        startDate = defaultStartDate;
        endDate = defaultEndDate;
    }
    
    return await new Promise((resolve, reject) => {
        
        const params = {
            'start_date': startDate,
            'end_date': endDate,
        };

        const url = new URL(`${window.location.origin}/events/byperiod`);

        Object
            .keys(params)
            .forEach((key) =>
                url.searchParams.append(key, params[key])
            );

        fetch(url.toString(), {
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

        findByDate(startDate, endDate) {
            if (!(typeof startDate === 'string' && typeof endDate === 'string' )) {
                startDate = document.querySelector("#start_date").value;
                endDate = document.querySelector("#end_date").value;
            }

            if (!(typeof startDate === 'string' && typeof endDate === 'string' )) {
                const message = "Valores necessários, datas de início e fim!";
                alert(message);
                throw new Error(message);
            }

            if ((new Date(endDate)) <= (new Date(startDate))) {
                const message = "A data do fim não pode ser anterior a de início...";
                alert(message);
                throw new Error(message);
            }

            (async () => {
                let data = await fetchEvents(startDate, endDate);

                this.eventItems = data;

                setTimeout(() => {
                    const element = document.getElementById("list-events");
            
                    element?.scrollIntoView({ behavior: "smooth", block: "end" });
                }, 250);
            })();
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