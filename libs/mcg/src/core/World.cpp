/**
 * @file World.cpp
 * @brief This file implements the methods in the World class.
 */
#include <fstream>
#include <iostream>

#include "mcg/World.h"

using namespace std;
using json = nlohmann::json;

World::World() {}

mt19937_64& World::getRandom() { return this->gen; }

void World::setRandom(int seed) {
    mt19937_64 newGen(seed);
    this->gen = newGen;
}

vector<shared_ptr<AABB>>& World::getAABBList() { return (this->aabbs); }

vector<shared_ptr<Block>>& World::getBlocks() { return (this->blocks); }

vector<shared_ptr<Entity>>& World::getEntities() { return this->entities; }

vector<shared_ptr<Object>>& World::getObjects() { return this->objects; }

vector<shared_ptr<Connection>>& World::getConnections() {
    return this->connections;
}

void World::addAABB(AABB& aabb) {
    (this->aabbs).push_back(make_shared<AABB>(aabb));
}

void World::addBlock(Block& block) {
    (this->blocks).push_back(make_shared<Block>(block));
}

void World::addEntity(Entity& entity) {
    (this->entities).push_back(make_shared<Entity>(entity));
}

void World::addObject(Object& object) {
    (this->objects).push_back(make_shared<Object>(object));
}

void World::addConnection(Connection& connection) {
    (this->connections).push_back(make_shared<Connection>(connection));
}

string World::toLowLevelMapJSON() {
    json world_json;

    vector<json> locations;
    vector<json> entities;

    world_json["blocks"] = locations;
    world_json["entities"] = entities;

    // Add AABBs to the JSON list
    for (auto aabb : this->aabbs) {
        aabb->toLowLevelMapJSON(world_json);
    }

    for (auto block : this->getBlocks()) {
        block->toLowLevelMapJSON(world_json);
    }

    for (auto entity : this->getEntities()) {
        entity->toLowLevelMapJSON(world_json);
    }

    for (auto object : this->getObjects()) {
        object->toLowLevelMapJSON(world_json);
    }

    return world_json.dump();
}

string World::toSemanticMapJSON() {
    json world_json;

    vector<json> locations;
    vector<json> entities;
    vector<json> objects;
    vector<json> connections;

    world_json["locations"] = locations;
    world_json["entities"] = entities;
    world_json["objects"] = objects;
    world_json["connections"] = connections;

    // Add AABBs to the JSON list
    for (auto& aabb : this->aabbs) {
        aabb->toSemanticMapJSON(world_json);
    }

    for (auto& block : this->getBlocks()) {
        block->toSemanticMapJSON(world_json);
    }

    for (auto& entity : this->getEntities()) {
        entity->toSemanticMapJSON(world_json);
    }

    for (auto& object : this->getObjects()) {
        object->toSemanticMapJSON(world_json);
    }

    for (auto& connection : this->getConnections()) {
        connection->toSemanticMapJSON(world_json);
    }

    return world_json.dump();
}

void World::writeToFile(string jsonPath, string altJSONPath) {
    cout << "Writing to file..." << endl;

    // Write JSON
    ofstream outputJSON(jsonPath, ios::out);
    outputJSON << this->toSemanticMapJSON();
    outputJSON.close();

    // Write TSV
    ofstream outputLowLevelMapJSON(altJSONPath, ios::out);
    outputLowLevelMapJSON << this->toLowLevelMapJSON();
    outputLowLevelMapJSON.close();
}

World::~World() {}
