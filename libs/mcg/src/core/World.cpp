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
    (this->aabbs).push_back(make_shared<AABB>(move(aabb)));
}

void World::addBlock(Block& block) {
    (this->blocks).push_back(make_shared<Block>(move(block)));
}

void World::addEntity(Entity& entity) {
    (this->entities).push_back(make_shared<Entity>(move(entity)));
}

void World::addObject(Object& object) {
    (this->objects).push_back(make_shared<Object>(move(object)));
}

void World::addConnection(Connection& connection) {
    (this->connections).push_back(make_shared<Connection>(move(connection)));
}

string World::toLowLevelMapJSON() {
    json world_json;

    vector<json> location_list;
    vector<json> entity_list;

    world_json["blocks"] = location_list;
    world_json["entities"] = entity_list;

    // Add AABBs to the JSON list
    for (auto& aabbPtr : this->aabbs) {
        (*aabbPtr).toLowLevelMapJSON(world_json);
    }

    for (auto& blockPtr : this->getBlocks()) {
        (*blockPtr).toLowLevelMapJSON(world_json);
    }

    for (auto& entityPtr : this->getEntities()) {
        (*entityPtr).toLowLevelMapJSON(world_json);
    }

    for (auto& objectPtr : this->getObjects()) {
        (*objectPtr).toLowLevelMapJSON(world_json);
    }

    return world_json.dump();
}

string World::toSemanticMapJSON() {
    json world_json;

    vector<json> location_list;
    vector<json> entity_list;
    vector<json> object_list;
    vector<json> connection_list;

    world_json["locations"] = location_list;
    world_json["entities"] = entity_list;
    world_json["objects"] = object_list;
    world_json["connections"] = connection_list;

    // Add AABBs to the JSON list
    for (auto& aabbPtr : this->aabbs) {
        (*aabbPtr).toSemanticMapJSON(world_json);
    }

    for (auto& blockPtr : this->getBlocks()) {
        (*blockPtr).toSemanticMapJSON(world_json);
    }

    for (auto& entityPtr : this->getEntities()) {
        (*entityPtr).toSemanticMapJSON(world_json);
    }

    for (auto& objectPtr : this->getObjects()) {
        (*objectPtr).toSemanticMapJSON(world_json);
    }

    for (auto& connectionPtr : this->getConnections()) {
        (*connectionPtr).toSemanticMapJSON(world_json);
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
