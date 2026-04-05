"""
GraphQL Task Service — FastAPI + Strawberry
Entry point for the microservice.
"""

import strawberry
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

from app.graphql.schema import schema


def create_app() -> FastAPI:
    app = FastAPI(
        title="GraphQL Task Service",
        description="Cloud-native microservice with a GraphQL API for task management.",
        version="1.0.0",
    )

    graphql_router = GraphQLRouter(schema, graphql_ide="graphiql")
    app.include_router(graphql_router, prefix="/graphql")

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "service": "graphql-taskservice"}

    return app


app = create_app()
