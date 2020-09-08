#include "F1Score.h"

namespace tomcat {
    namespace model {

        using namespace std;

        //----------------------------------------------------------------------
        // Constructors & Destructor
        //----------------------------------------------------------------------
        F1Score::F1Score(shared_ptr<Estimator> estimator, double threshold)
            : Measure(estimator, threshold) {}

        F1Score::~F1Score() {}

        //----------------------------------------------------------------------
        // Copy & Move constructors/assignments
        //----------------------------------------------------------------------
        F1Score::F1Score(const F1Score& f1_score) {
            this->copy_measure(f1_score);
        }

        F1Score& F1Score::operator=(const F1Score& f1_score) {
            this->copy_measure(f1_score);
            return *this;
        }

        //----------------------------------------------------------------------
        // Member functions
        //----------------------------------------------------------------------
        vector<NodeEvaluation>
        F1Score::evaluate(const EvidenceSet& test_data) const {
            vector<NodeEvaluation> evaluations;

            for (const auto& estimates :
                 this->estimator->get_estimates()) {
                NodeEvaluation evaluation;
                evaluation.label = estimates.label;
                evaluation.assignment = estimates.assignment;

                ConfusionMatrix confusion_matrix =
                    this->get_confusion_matrix(estimates, test_data);
                double precision = 0;
                if (confusion_matrix.true_positives + confusion_matrix.false_positives > 0) {
                    precision = (double)confusion_matrix.true_positives /
                                (confusion_matrix.true_positives + confusion_matrix.false_positives);
                }

                double recall = 0;
                if (confusion_matrix.true_positives + confusion_matrix.false_negatives > 0) {
                    recall = (double)confusion_matrix.true_positives /
                                (confusion_matrix.true_positives + confusion_matrix.false_negatives);
                }

                double f1_score = 0;
                if (precision > 0 and recall > 0) {
                    f1_score = (2 * precision * recall) / (precision + recall);
                }

                evaluation.evaluation =
                    Eigen::MatrixXd::Constant(1, 1, f1_score);
                evaluations.push_back(evaluation);
            }

            return evaluations;
        }

        void F1Score::get_info(nlohmann::json& json) const {
            json["name"] = "f1 score";
            json["threshold"] = this->threshold;
            this->estimator->get_info(json["estimator"]);
        }

    } // namespace model
} // namespace tomcat
