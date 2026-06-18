/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class CompanyKnowledgeDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            loading: true,
            query: "",
            selectedCategoryId: false,
            stateFilter: false,
            quickFilter: false,
            categories: [],
            articles: [],
            counters: {},
            selectedCategory: false,
            sortBy: "updated",
            limit: 40,
        });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    _safeDomain(domain) {
        return Array.isArray(domain) ? domain : [];
    }

    _safeContext(context) {
        return context && typeof context === "object" ? context : {};
    }

    _defaultArticleViews() {
        return [[false, "list"], [false, "kanban"], [false, "form"], [false, "pivot"], [false, "graph"]];
    }

    async loadData() {
        this.state.loading = true;
        try {
            const data = await this.orm.call(
                "company.knowledge.article",
                "get_dashboard_sidebar_data",
                [],
                {
                    category_id: this.state.selectedCategoryId || false,
                    query: this.state.query || false,
                    state_filter: this.state.stateFilter || false,
                    quick_filter: this.state.quickFilter || false,
                    sort_by: this.state.sortBy || false,
                    limit: this.state.limit,
                }
            );
            this.state.categories = data.categories || [];
            this.state.articles = data.articles || [];
            this.state.counters = data.counters || {};
            this.state.selectedCategory = data.selected_category || false;
            this.state.sortBy = data.sort_by || this.state.sortBy;
        } catch (error) {
            this.notification.add("Impossibile caricare la dashboard Knowledge Base.", {
                type: "danger",
            });
            throw error;
        } finally {
            this.state.loading = false;
        }
    }

    async selectCategory(categoryId) {
        this.state.selectedCategoryId = categoryId || false;
        await this.loadData();
    }

    async clearCategory() {
        this.state.selectedCategoryId = false;
        await this.loadData();
    }

    async setStateFilter(filterName) {
        this.state.stateFilter = filterName || false;
        this.state.quickFilter = false;
        await this.loadData();
    }

    async setQuickFilter(filterName) {
        this.state.quickFilter = filterName || false;
        this.state.stateFilter = false;
        await this.loadData();
    }

    async onSearchInput(ev) {
        this.state.query = ev.target.value;
    }

    async onSearchKeydown(ev) {
        if (ev.key === "Enter") {
            await this.loadData();
        }
    }

    async clearSearch() {
        this.state.query = "";
        await this.loadData();
    }

    async setSortBy(ev) {
        this.state.sortBy = ev.target.value || "updated";
        await this.loadData();
    }

    openArticle(articleId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Articolo Knowledge Base",
            res_model: "company.knowledge.article",
            res_id: articleId,
            views: [[false, "form"]],
            view_mode: "form",
            target: "current",
            domain: [],
            context: {},
        });
    }

    openArticleList(extraDomain = [], title = "Articoli") {
        const domain = [["active", "=", true], ...this._safeDomain(extraDomain)];

        if (this.state.selectedCategoryId) {
            domain.push(["category_id", "child_of", this.state.selectedCategoryId]);
        }

        if (this.state.query) {
            domain.push("|");
            domain.push("|");
            domain.push(["name", "ilike", this.state.query]);
            domain.push(["summary", "ilike", this.state.query]);
            domain.push(["body_html", "ilike", this.state.query]);
        }

        this.action.doAction({
            type: "ir.actions.act_window",
            name: title,
            res_model: "company.knowledge.article",
            views: this._defaultArticleViews(),
            view_mode: "list,kanban,form,pivot,graph",
            domain: domain,
            context: {},
            target: "current",
        });
    }

    async openCurrentSelection() {
        try {
            const action = await this.orm.call(
                "company.knowledge.article",
                "get_dashboard_article_action",
                [],
                {
                    category_id: this.state.selectedCategoryId || false,
                    query: this.state.query || false,
                    state_filter: this.state.stateFilter || false,
                    quick_filter: this.state.quickFilter || false,
                    sort_by: this.state.sortBy || false,
                }
            );

            this.action.doAction({
                type: "ir.actions.act_window",
                name: (action && action.name) || "Articoli Knowledge Base",
                res_model: "company.knowledge.article",
                views: Array.isArray(action && action.views) ? action.views : this._defaultArticleViews(),
                view_mode: (action && action.view_mode) || "list,kanban,form,pivot,graph",
                domain: this._safeDomain(action && action.domain),
                context: this._safeContext(action && action.context),
                target: (action && action.target) || "current",
            });
        } catch (error) {
            this.notification.add("Impossibile aprire l'elenco degli articoli.", {
                type: "danger",
            });
            throw error;
        }
    }
}

CompanyKnowledgeDashboard.template = "company_knowledge_base.CompanyKnowledgeDashboard";

registry.category("actions").add("company_knowledge_dashboard", CompanyKnowledgeDashboard);
