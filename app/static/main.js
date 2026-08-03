function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function sanitizeValue(value) {
    if (typeof value === "string") {
        return escapeHtml(value);
    }

    if (Array.isArray(value)) {
        return value.map(sanitizeValue);
    }

    if (value && typeof value === "object") {
        return Object.fromEntries(
            Object.entries(value).map(([key, item]) => [key, sanitizeValue(item)])
        );
    }

    return value;
}

const api = {
    async get(path) {
        const response = await fetch(path);
        const body = await response.json();

        if (!response.ok) {
            throw new Error(body.error || "Request failed");
        }

        return sanitizeValue(body);
    },
    async send(path, method, data) {
        const response = await fetch(path, {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        const body = await response.json();

        if (!response.ok) {
            throw new Error(body.error || "Request failed");
        }

        return sanitizeValue(body);
    }
};

function formatMoney(value) {
    return `€${Number(value).toFixed(2)}`;
}

function imageMarkup(concert, className, altPrefix = "Concert image for") {
    if (!concert.image_url) return "";
    return `<img class="${className}" src="${concert.image_url}" alt="${altPrefix} ${concert.title}">`;
}

function concertCard(concert) {
    return `
        <article class="card">
            ${imageMarkup(concert, "card-image")}
            <h3>${concert.title}</h3>
            <div class="meta">${concert.artist}</div>
            <div>${concert.venue} | ${concert.concert_date}</div>
            <div class="price">${formatMoney(concert.price)}</div>
            <div>${concert.seats_available} seats left</div>
            <a class="button" href="/concerts/${concert.id}">Details</a>
        </article>
    `;
}

async function loadFeaturedConcerts() {
    const container = document.querySelector("#featuredConcerts");
    if (!container) return;
    const concerts = await api.get("/api/concerts");
    container.innerHTML = concerts.slice(0, 6).map(concertCard).join("");
}

async function loadConcerts() {
    const container = document.querySelector("#concertList");
    if (!container) return;
    const concerts = await api.get("/api/concerts");
    container.innerHTML = concerts.map(concertCard).join("");
}

async function loadConcertDetails() {
    const container = document.querySelector("#concertDetails");
    const concertId = document.querySelector("#concertId")?.value;
    if (!container || !concertId) return;
    const concert = await api.get(`/api/concerts/${concertId}`);
    container.innerHTML = `
        ${imageMarkup(concert, "details-image", "Concert image for")}
        <h1>${concert.title}</h1>
        <p class="meta">${concert.artist} at ${concert.venue}</p>
        <p><strong>Date:</strong> ${concert.concert_date}</p>
        <p><strong>Price:</strong> ${formatMoney(concert.price)}</p>
        <p><strong>Seats available:</strong> ${concert.seats_available}</p>
        <p>${concert.description}</p>
    `;
}

function setupBookingForm() {
    const form = document.querySelector("#bookingForm");
    if (!form) return;
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const message = document.querySelector("#bookingMessage");
        try {
            const result = await api.send("/api/bookings", "POST", {
                concert_id: document.querySelector("#concertId").value,
                customer_name: document.querySelector("#customerName").value,
                customer_email: document.querySelector("#customerEmail").value,
                tickets: document.querySelector("#ticketCount").value
            });
            message.textContent = `${result.message}. ${result.notification.message || ""}`;
            form.reset();
            await loadConcertDetails();
        } catch (error) {
            message.textContent = error.message;
        }
    });
}

async function loadBookings() {
    const container = document.querySelector("#bookingList");
    if (!container) return;
    const bookings = await api.get("/api/bookings");
    if (bookings.length === 0) {
        container.innerHTML = "<p>No bookings yet.</p>";
        return;
    }
    container.innerHTML = bookings.map((booking) => `
        <article class="booking-row">
            <div>
                <strong>${booking.title}</strong><br>
                ${booking.customer_name} | ${booking.tickets} ticket(s)<br>
                <span class="meta">${booking.venue} | ${booking.concert_date}</span>
            </div>
            <button class="danger" data-delete-booking="${booking.id}">Cancel</button>
        </article>
    `).join("");
}

function setupBookingDelete() {
    document.addEventListener("click", async (event) => {
        const id = event.target.dataset.deleteBooking;
        if (!id) return;
        await api.send(`/api/bookings/${id}`, "DELETE", {});
        await loadBookings();
    });
}

function getConcertFormData() {
    return {
        title: document.querySelector("#title").value,
        artist: document.querySelector("#artist").value,
        venue: document.querySelector("#venue").value,
        concert_date: document.querySelector("#concertDate").value,
        price: document.querySelector("#price").value,
        seats_available: document.querySelector("#seatsAvailable").value,
        description: document.querySelector("#description").value,
        image_url: document.querySelector("#imageUrl").value
    };
}

function fillConcertForm(concert) {
    document.querySelector("#adminConcertId").value = concert.id;
    document.querySelector("#title").value = concert.title;
    document.querySelector("#artist").value = concert.artist;
    document.querySelector("#venue").value = concert.venue;
    document.querySelector("#concertDate").value = concert.concert_date;
    document.querySelector("#price").value = concert.price;
    document.querySelector("#seatsAvailable").value = concert.seats_available;
    document.querySelector("#description").value = concert.description;
    document.querySelector("#imageUrl").value = concert.image_url;
}

function clearConcertForm() {
    document.querySelector("#concertForm")?.reset();
    const id = document.querySelector("#adminConcertId");
    if (id) id.value = "";
}

async function loadAdminConcerts() {
    const container = document.querySelector("#adminConcertList");
    if (!container) return;
    const concerts = await api.get("/api/concerts");
    container.innerHTML = concerts.map((concert) => `
        <article class="booking-row">
            <div>
                <strong>${concert.title}</strong><br>
                ${concert.artist} | ${concert.concert_date}<br>
                <span class="meta">${concert.seats_available} seats | ${formatMoney(concert.price)}</span>
            </div>
            <div class="actions">
                <button class="secondary" data-edit-concert="${concert.id}">Edit</button>
                <button class="danger" data-delete-concert="${concert.id}">Delete</button>
            </div>
        </article>
    `).join("");
}

function setupAdmin() {
    const form = document.querySelector("#concertForm");
    if (!form) return;
    const message = document.querySelector("#adminMessage");

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const id = document.querySelector("#adminConcertId").value;
        const method = id ? "PUT" : "POST";
        const path = id ? `/api/concerts/${id}` : "/api/concerts";
        try {
            const result = await api.send(path, method, getConcertFormData());
            message.textContent = result.message;
            clearConcertForm();
            await loadAdminConcerts();
        } catch (error) {
            message.textContent = error.message;
        }
    });

    document.querySelector("#clearForm").addEventListener("click", clearConcertForm);

    document.addEventListener("click", async (event) => {
        const editId = event.target.dataset.editConcert;
        const deleteId = event.target.dataset.deleteConcert;
        if (editId) {
            fillConcertForm(await api.get(`/api/concerts/${editId}`));
        }
        if (deleteId) {
            await api.send(`/api/concerts/${deleteId}`, "DELETE", {});
            await loadAdminConcerts();
        }
    });
}

document.addEventListener("DOMContentLoaded", async () => {
    setupBookingForm();
    setupBookingDelete();
    setupAdmin();
    await loadFeaturedConcerts();
    await loadConcerts();
    await loadConcertDetails();
    await loadBookings();
    await loadAdminConcerts();
});

