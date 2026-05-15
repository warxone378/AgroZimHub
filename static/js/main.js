// Language translations
const translations = {
    en: {
        app_name: "AgroZim Hub",
        home: "Home",
        predictor: "AI Predictor",
        marketplace: "Marketplace",
        warnings: "Warnings",
        agronomists: "Agronomists",
        login: "Login",
        register: "Register",
        logout: "Logout",
        welcome: "Welcome to AgroZim Hub",
        welcome_sub: "Empowering Zimbabwean Agriculture",
        get_started: "Get Started",
        ai_planting_advice: "AI Planting Advisor",
        flood_warning: "Flood Warning",
        dry_spell: "Dry Spell",
        chat_on_whatsapp: "Chat on WhatsApp",
        order_quantity: "Order Quantity (kg)",
        contact_seller: "Contact Seller",
        view_details: "View Details",
        edit: "Edit",
        delete: "Delete",
        create_listing: "Create Listing",
        filter_by_location: "Filter by Location",
        search_products: "Search products...",
        all_locations: "All Locations",
        apply_filters: "Apply Filters",
        phone: "Phone",
        location: "Location",
        role: "Role",
        province: "Province",
        soil_ph: "Soil pH",
        soil_type: "Soil Type",
        hectares: "Hectares",
        seed_type: "Seed Type",
        get_recommendation: "Get AI Recommendation"
    },
    sn: {
        app_name: "AgroZim Hub",
        home: "Kumba",
        predictor: "AI Inoratidza",
        marketplace: "Musika",
        warnings: "Nyevero",
        agronomists: "Agronomisti",
        login: "Pinda",
        register: "Nyoresa",
        logout: "Zviba",
        welcome: "Takugashira kuAgroZim Hub",
        welcome_sub: "Kusimudzira Kurima muZimbabwe",
        get_started: "Tanga",
        ai_planting_advice: "AI Zano Rekurima",
        flood_warning: "Nyevero yeMafashamo",
        dry_spell: "Kusanaya kwemvura",
        chat_on_whatsapp: "Taura paWhatsApp",
        order_quantity: "Hu wandinoda (kg)",
        contact_seller: "Bata Mutengesi",
        view_details: "Ona Zvakadzama",
        edit: "Chinja",
        delete: "Bvisa",
        create_listing: "Isa Chiripo",
        filter_by_location: "Sefa nenzvimbo",
        search_products: "Tsvaga zvigadzirwa...",
        all_locations: "Nzvimbo dzose",
        apply_filters: "Shandisa Sefa",
        phone: "Runhare",
        location: "Nzvimbo",
        role: "Basa",
        province: "Dunhu",
        soil_ph: "Ivhu pH",
        soil_type: "Rudzi rweIvhu",
        hectares: "Mahekita",
        seed_type: "Rudzi rweMbeu",
        get_recommendation: "Tora Zano reAI"
    },
    nd: {
        app_name: "AgroZim Hub",
        home: "Ekhaya",
        predictor: "AI Isibikezeli",
        marketplace: "Imakethe",
        warnings: "Izexwayiso",
        agronomists: "Ongoti Bezolimo",
        login: "Ngena",
        register: "Bhalisa",
        logout: "Phuma",
        welcome: "Siyakwemukela kuAgroZim Hub",
        welcome_sub: "Ukuqinisa Ezolimo eZimbabwe",
        get_started: "Qala",
        ai_planting_advice: "AI Iseluleko Sokutshala",
        flood_warning: "Isexwayiso Sezikhukhula",
        dry_spell: "Ukoma",
        chat_on_whatsapp: "Khuluma ngeWhatsApp",
        order_quantity: "Inani (kg)",
        contact_seller: "Xhumana noMdayisi",
        view_details: "Bona Imininingwane",
        edit: "Hlela",
        delete: "Susa",
        create_listing: "Dala Uhlu",
        filter_by_location: "Hlunga ngendawo",
        search_products: "Sesha imikhiqizo...",
        all_locations: "Zonke izindawo",
        apply_filters: "Sebenzisa Ukuhlunga",
        phone: "Ucingo",
        location: "Indawo",
        role: "Indima",
        province: "Isifundazwe",
        soil_ph: "Inhlabathi pH",
        soil_type: "Uhlobo Lwenhlabathi",
        hectares: "Amahektha",
        seed_type: "Uhlobo Lwembewu",
        get_recommendation: "Thola Iseluleko se-AI"
    }
};

let currentLang = localStorage.getItem('language') || 'en';

function setLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('language', lang);
    
    // Update all elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        if (translations[lang] && translations[lang][key]) {
            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                element.placeholder = translations[lang][key];
            } else {
                element.textContent = translations[lang][key];
            }
        }
    });
    
    // Update active class on language buttons
    document.querySelectorAll('.lang-btn').forEach(btn => {
        if (btn.getAttribute('data-lang') === lang) {
            btn.classList.add('active', 'text-emerald');
        } else {
            btn.classList.remove('active', 'text-emerald');
        }
    });
}

// Initialize language on page load
document.addEventListener('DOMContentLoaded', () => {
    setLanguage(currentLang);
    
    // Setup WhatsApp chat with order quantity
    document.querySelectorAll('.whatsapp-chat').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const phone = btn.getAttribute('data-phone');
            const quantity = document.getElementById(`qty-${btn.getAttribute('data-listing-id')}`)?.value || 'some';
            const crop = btn.getAttribute('data-crop');
            const message = `Hello, I'm interested in buying ${quantity} kg of ${crop}. Please let me know if available.`;
            const whatsappUrl = `https://wa.me/${phone}?text=${encodeURIComponent(message)}`;
            window.open(whatsappUrl, '_blank');
        });
    });
});
